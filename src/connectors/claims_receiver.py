"""
Conector para receber sinistros de múltiplos canais
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod
import json

from ..database.connection import get_db_session
from ..database.models import Sinistro, StatusSinistro
from ..workers.tasks import processar_sinistro_async
from ..monitoring.metrics import track_metric, track_error

logger = logging.getLogger(__name__)

class BaseClaimsReceiver(ABC):
    """Classe base para receber sinistros de diferentes canais"""
    
    @abstractmethod
    def validate_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e normaliza dados do sinistro"""
        pass
    
    @abstractmethod
    def transform_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma dados para formato interno"""
        pass
    
    def receive_claim(self, raw_data: Dict[str, Any], source: str) -> Optional[str]:
        """
        Recebe sinistro de qualquer fonte e processa
        Retorna número do sinistro criado
        """
        try:
            # 1. Validar dados
            validated_data = self.validate_claim_data(raw_data)
            
            # 2. Transformar para formato interno
            claim_data = self.transform_claim_data(validated_data)
            
            # 3. Adicionar metadados
            claim_data['canal_origem'] = source
            claim_data['sistema_origem'] = self.__class__.__name__
            claim_data['metadata'] = {
                'raw_data': raw_data,
                'received_at': datetime.now().isoformat(),
                'source': source
            }
            
            # 4. Criar sinistro no banco
            numero_sinistro = self._create_claim(claim_data)
            
            # 5. Iniciar processamento assíncrono
            self._start_processing(numero_sinistro)
            
            # 6. Métricas
            track_metric("sinistro_recebido", 1, {"canal": source, "receiver": self.__class__.__name__})
            
            logger.info(f"Sinistro {numero_sinistro} recebido de {source}")
            return numero_sinistro
            
        except Exception as e:
            logger.error(f"Erro ao receber sinistro de {source}: {str(e)}")
            track_error("erro_receber_sinistro", e, {"source": source})
            raise
    
    def _create_claim(self, claim_data: Dict[str, Any]) -> str:
        """Cria sinistro no banco de dados"""
        import uuid
        
        with get_db_session() as db:
            numero_sinistro = f"SIN-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
            
            sinistro = Sinistro(
                numero_sinistro=numero_sinistro,
                status=StatusSinistro.RECEBIDO,
                data_ocorrencia=claim_data['data_ocorrencia'],
                segurado_nome=claim_data['segurado_nome'],
                segurado_documento=claim_data['segurado_documento'],
                segurado_telefone=claim_data.get('segurado_telefone'),
                segurado_email=claim_data.get('segurado_email'),
                apolice_numero=claim_data['apolice_numero'],
                descricao=claim_data['descricao'],
                local_ocorrencia=claim_data.get('local_ocorrencia'),
                valor_estimado=claim_data.get('valor_estimado', 0),
                canal_origem=claim_data['canal_origem'],
                sistema_origem=claim_data['sistema_origem'],
                metadata=claim_data.get('metadata', {})
            )
            
            db.add(sinistro)
            db.commit()
            
            return numero_sinistro
    
    def _start_processing(self, numero_sinistro: str):
        """Inicia processamento assíncrono"""
        processar_sinistro_async.delay(numero_sinistro)


class LegacySystemReceiver(BaseClaimsReceiver):
    """Recebe sinistros do sistema legado"""
    
    def validate_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados do sistema legado"""
        required_fields = ['PolicyNumber', 'ClaimDate', 'InsuredName', 'InsuredDocument']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo obrigatório ausente: {field}")
        
        return data
    
    def transform_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma formato legado para formato interno"""
        return {
            'data_ocorrencia': datetime.fromisoformat(data['ClaimDate']),
            'segurado_nome': data['InsuredName'],
            'segurado_documento': data['InsuredDocument'],
            'segurado_telefone': data.get('InsuredPhone'),
            'segurado_email': data.get('InsuredEmail'),
            'apolice_numero': data['PolicyNumber'],
            'descricao': data.get('Description', 'Sinistro importado do sistema legado'),
            'local_ocorrencia': data.get('Location'),
            'valor_estimado': float(data.get('EstimatedAmount', 0))
        }


class WebFormReceiver(BaseClaimsReceiver):
    """Recebe sinistros de formulário web"""
    
    def validate_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados do formulário web"""
        # Validação específica para formulário web
        if not data.get('consentimento_lgpd'):
            raise ValueError("Consentimento LGPD é obrigatório")
        
        # Validar email
        import re
        if data.get('email') and not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
            raise ValueError("Email inválido")
        
        return data
    
    def transform_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma dados do formulário web"""
        return {
            'data_ocorrencia': datetime.fromisoformat(data['dataOcorrencia']),
            'segurado_nome': data['nome'],
            'segurado_documento': data['cpf'].replace('.', '').replace('-', ''),
            'segurado_telefone': data.get('telefone'),
            'segurado_email': data.get('email'),
            'apolice_numero': data['numeroApolice'],
            'descricao': data['descricao'],
            'local_ocorrencia': f"{data.get('endereco', '')}, {data.get('cidade', '')}/{data.get('estado', '')}",
            'valor_estimado': float(data.get('valorEstimado', 0))
        }


class MobileAppReceiver(BaseClaimsReceiver):
    """Recebe sinistros do app mobile"""
    
    def validate_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados do app mobile"""
        # Validar token de autenticação
        if not data.get('auth_token'):
            raise ValueError("Token de autenticação ausente")
        
        # Validar geolocalização se presente
        if 'location' in data:
            lat = data['location'].get('latitude')
            lon = data['location'].get('longitude')
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError("Coordenadas inválidas")
        
        return data
    
    def transform_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma dados do app mobile"""
        transformed = {
            'data_ocorrencia': datetime.fromtimestamp(data['timestamp']),
            'segurado_nome': data['user']['name'],
            'segurado_documento': data['user']['document'],
            'segurado_telefone': data['user']['phone'],
            'segurado_email': data['user']['email'],
            'apolice_numero': data['policy_number'],
            'descricao': data['description'],
            'valor_estimado': float(data.get('estimated_value', 0))
        }
        
        # Adicionar localização se disponível
        if 'location' in data:
            transformed['local_ocorrencia'] = f"Lat: {data['location']['latitude']}, Lon: {data['location']['longitude']}"
            transformed['metadata'] = {
                'location': data['location'],
                'device_info': data.get('device_info', {})
            }
        
        return transformed


class EmailReceiver(BaseClaimsReceiver):
    """Recebe sinistros via email"""
    
    def validate_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados do email"""
        if not data.get('from_email'):
            raise ValueError("Email do remetente ausente")
        
        if not data.get('subject'):
            raise ValueError("Assunto do email ausente")
        
        return data
    
    def transform_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai informações do email"""
        # Parser simples - em produção usar NLP
        body = data.get('body', '')
        
        # Extrair informações básicas
        import re
        
        # Tentar extrair CPF
        cpf_match = re.search(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', body)
        cpf = cpf_match.group(0) if cpf_match else 'PENDENTE'
        
        # Tentar extrair apólice
        apolice_match = re.search(r'ap[óo]lice:?\s*(\S+)', body, re.IGNORECASE)
        apolice = apolice_match.group(1) if apolice_match else 'PENDENTE'
        
        return {
            'data_ocorrencia': datetime.now(),  # Usar data do email
            'segurado_nome': data.get('from_name', 'PENDENTE'),
            'segurado_documento': cpf,
            'segurado_email': data['from_email'],
            'apolice_numero': apolice,
            'descricao': f"Assunto: {data['subject']}\n\nCorpo: {body[:1000]}",
            'valor_estimado': 0,
            'metadata': {
                'email_id': data.get('email_id'),
                'attachments': data.get('attachments', [])
            }
        }


class BatchFileReceiver(BaseClaimsReceiver):
    """Recebe sinistros via arquivo batch (CSV/Excel)"""
    
    def validate_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida linha do arquivo batch"""
        # Validações específicas para batch
        if not data.get('linha_numero'):
            raise ValueError("Número da linha ausente")
        
        return data
    
    def transform_claim_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma linha do batch"""
        return {
            'data_ocorrencia': datetime.strptime(data['DATA_SINISTRO'], '%d/%m/%Y'),
            'segurado_nome': data['NOME_SEGURADO'],
            'segurado_documento': data['CPF_CNPJ'],
            'segurado_telefone': data.get('TELEFONE'),
            'segurado_email': data.get('EMAIL'),
            'apolice_numero': data['NUMERO_APOLICE'],
            'descricao': data.get('DESCRICAO', 'Importado via batch'),
            'local_ocorrencia': data.get('LOCAL'),
            'valor_estimado': float(data.get('VALOR', 0)),
            'metadata': {
                'batch_file': data.get('arquivo_origem'),
                'linha': data.get('linha_numero')
            }
        }


class ClaimsReceiverFactory:
    """Factory para criar receivers apropriados"""
    
    _receivers = {
        'legacy': LegacySystemReceiver,
        'web': WebFormReceiver,
        'mobile': MobileAppReceiver,
        'email': EmailReceiver,
        'batch': BatchFileReceiver
    }
    
    @classmethod
    def get_receiver(cls, source_type: str) -> BaseClaimsReceiver:
        """Retorna receiver apropriado para o tipo de fonte"""
        receiver_class = cls._receivers.get(source_type)
        if not receiver_class:
            raise ValueError(f"Tipo de fonte não suportado: {source_type}")
        
        return receiver_class()
    
    @classmethod
    def register_receiver(cls, source_type: str, receiver_class: type):
        """Registra novo tipo de receiver"""
        cls._receivers[source_type] = receiver_class


# Função principal para receber sinistros
def receive_claim_from_channel(source_type: str, data: Dict[str, Any]) -> str:
    """
    Função principal para receber sinistros de qualquer canal
    
    Args:
        source_type: Tipo da fonte (legacy, web, mobile, email, batch)
        data: Dados do sinistro no formato da fonte
    
    Returns:
        Número do sinistro criado
    """
    try:
        receiver = ClaimsReceiverFactory.get_receiver(source_type)
        numero_sinistro = receiver.receive_claim(data, source_type)
        
        logger.info(f"Sinistro {numero_sinistro} recebido com sucesso de {source_type}")
        return numero_sinistro
        
    except Exception as e:
        logger.error(f"Erro ao processar sinistro de {source_type}: {str(e)}")
        raise
