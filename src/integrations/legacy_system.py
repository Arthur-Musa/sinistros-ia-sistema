"""
Integração com sistemas legados
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config.settings import get_settings
from ..database.models import Sinistro, StatusSinistro
from ..monitoring.metrics import track_metric, track_error

logger = logging.getLogger(__name__)
settings = get_settings()

class LegacySystemClient:
    """Cliente para integração com sistema legado"""
    
    def __init__(self):
        self.base_url = settings.LEGACY_SYSTEM_URL
        self.api_key = settings.LEGACY_SYSTEM_API_KEY
        self.timeout = settings.LEGACY_SYSTEM_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def buscar_apolice(self, numero_apolice: str) -> Optional[Dict[str, Any]]:
        """
        Busca dados da apólice no sistema legado
        """
        try:
            response = self.session.get(
                f"{self.base_url}/apolices/{numero_apolice}",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            apolice_data = response.json()
            
            # Mapear dados do sistema legado para nosso formato
            return {
                "numero": apolice_data.get("PolicyNumber"),
                "produto": apolice_data.get("ProductName"),
                "vigencia_inicio": apolice_data.get("StartDate"),
                "vigencia_fim": apolice_data.get("EndDate"),
                "limite_cobertura": apolice_data.get("CoverageLimit"),
                "franquia": apolice_data.get("Deductible"),
                "status": apolice_data.get("Status"),
                "segurado": {
                    "nome": apolice_data.get("InsuredName"),
                    "documento": apolice_data.get("InsuredDocument"),
                    "telefone": apolice_data.get("InsuredPhone"),
                    "email": apolice_data.get("InsuredEmail")
                },
                "coberturas": apolice_data.get("Coverages", [])
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar apólice {numero_apolice}: {str(e)}")
            track_error("erro_buscar_apolice", e, {"numero_apolice": numero_apolice})
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def buscar_historico_sinistros(self, documento_segurado: str) -> List[Dict[str, Any]]:
        """
        Busca histórico de sinistros do segurado
        """
        try:
            response = self.session.get(
                f"{self.base_url}/segurados/{documento_segurado}/sinistros",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            sinistros = response.json()
            
            # Mapear lista de sinistros
            historico = []
            for sinistro in sinistros:
                historico.append({
                    "numero": sinistro.get("ClaimNumber"),
                    "data": sinistro.get("ClaimDate"),
                    "tipo": sinistro.get("ClaimType"),
                    "valor": sinistro.get("ClaimAmount"),
                    "status": sinistro.get("Status"),
                    "decisao": sinistro.get("Decision")
                })
            
            return historico
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar histórico do segurado {documento_segurado}: {str(e)}")
            return []
    
    def registrar_sinistro(self, sinistro: Sinistro) -> Optional[str]:
        """
        Registra sinistro no sistema legado
        """
        try:
            payload = {
                "ClaimNumber": sinistro.numero_sinistro,
                "PolicyNumber": sinistro.apolice_numero,
                "ClaimDate": sinistro.data_ocorrencia.isoformat(),
                "NotificationDate": sinistro.data_aviso.isoformat(),
                "InsuredDocument": sinistro.segurado_documento,
                "InsuredName": sinistro.segurado_nome,
                "Description": sinistro.descricao,
                "EstimatedAmount": sinistro.valor_estimado,
                "ClaimType": sinistro.tipo.value if sinistro.tipo else "outros",
                "Status": self._mapear_status(sinistro.status),
                "Channel": sinistro.canal_origem or "api",
                "ExternalMetadata": sinistro.metadata
            }
            
            response = self.session.post(
                f"{self.base_url}/sinistros",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            legacy_id = result.get("LegacyClaimId")
            
            logger.info(f"Sinistro {sinistro.numero_sinistro} registrado no sistema legado: {legacy_id}")
            track_metric("sinistro_registrado_legado", 1)
            
            return legacy_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao registrar sinistro {sinistro.numero_sinistro}: {str(e)}")
            track_error("erro_registrar_sinistro_legado", e)
            return None
    
    def atualizar_status_sinistro(self, numero_sinistro: str, status: StatusSinistro, 
                                  detalhes: Optional[Dict[str, Any]] = None) -> bool:
        """
        Atualiza status do sinistro no sistema legado
        """
        try:
            payload = {
                "Status": self._mapear_status(status),
                "UpdatedAt": datetime.now().isoformat(),
                "Details": detalhes or {}
            }
            
            response = self.session.patch(
                f"{self.base_url}/sinistros/{numero_sinistro}/status",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Status do sinistro {numero_sinistro} atualizado no sistema legado")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao atualizar status do sinistro {numero_sinistro}: {str(e)}")
            return False
    
    def enviar_documentos(self, numero_sinistro: str, documentos: List[Dict[str, Any]]) -> bool:
        """
        Envia referências de documentos para o sistema legado
        """
        try:
            payload = {
                "ClaimNumber": numero_sinistro,
                "Documents": [
                    {
                        "FileName": doc.get("nome"),
                        "FileType": doc.get("tipo"),
                        "Category": doc.get("categoria"),
                        "S3Path": doc.get("caminho_s3"),
                        "UploadDate": doc.get("data_upload"),
                        "Size": doc.get("tamanho_bytes")
                    }
                    for doc in documentos
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}/sinistros/{numero_sinistro}/documentos",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Documentos do sinistro {numero_sinistro} enviados ao sistema legado")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar documentos do sinistro {numero_sinistro}: {str(e)}")
            return False
    
    def buscar_dados_regulatorios(self, tipo_sinistro: str) -> Dict[str, Any]:
        """
        Busca regras e dados regulatórios para compliance
        """
        try:
            response = self.session.get(
                f"{self.base_url}/compliance/regras/{tipo_sinistro}",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar dados regulatórios para {tipo_sinistro}: {str(e)}")
            return {
                "prazos": {"analise": 30, "pagamento": 30},
                "documentos_obrigatorios": [],
                "limites": {}
            }
    
    def _mapear_status(self, status: StatusSinistro) -> str:
        """
        Mapeia status interno para status do sistema legado
        """
        mapeamento = {
            StatusSinistro.RECEBIDO: "RECEIVED",
            StatusSinistro.TRIAGEM: "TRIAGE",
            StatusSinistro.EM_ANALISE: "ANALYZING",
            StatusSinistro.DOCUMENTACAO_PENDENTE: "PENDING_DOCS",
            StatusSinistro.EM_CALCULO: "CALCULATING",
            StatusSinistro.EM_COMPLIANCE: "COMPLIANCE_CHECK",
            StatusSinistro.APROVADO: "APPROVED",
            StatusSinistro.NEGADO: "DENIED",
            StatusSinistro.CANCELADO: "CANCELLED",
            StatusSinistro.FINALIZADO: "CLOSED"
        }
        return mapeamento.get(status, "UNKNOWN")

# Instância global do cliente
legacy_client = LegacySystemClient()

def sincronizar_sinistro_com_legado(sinistro: Sinistro) -> bool:
    """
    Sincroniza sinistro completo com sistema legado
    """
    try:
        # 1. Buscar dados da apólice
        apolice_data = legacy_client.buscar_apolice(sinistro.apolice_numero)
        if apolice_data:
            # Atualizar dados do sinistro com informações da apólice
            sinistro.apolice_produto = apolice_data.get("produto")
            sinistro.metadata["apolice_dados"] = apolice_data
        
        # 2. Buscar histórico do segurado
        historico = legacy_client.buscar_historico_sinistros(sinistro.segurado_documento)
        if historico:
            sinistro.metadata["historico_sinistros"] = historico
            sinistro.metadata["qtd_sinistros_anteriores"] = len(historico)
        
        # 3. Registrar sinistro no sistema legado
        legacy_id = legacy_client.registrar_sinistro(sinistro)
        if legacy_id:
            sinistro.metadata["legacy_id"] = legacy_id
        
        # 4. Enviar documentos
        if sinistro.documentos:
            documentos_dict = [
                {
                    "nome": doc.nome,
                    "tipo": doc.tipo,
                    "categoria": doc.categoria,
                    "caminho_s3": doc.caminho_s3,
                    "tamanho_bytes": doc.tamanho_bytes,
                    "data_upload": doc.data_upload.isoformat()
                }
                for doc in sinistro.documentos
            ]
            legacy_client.enviar_documentos(sinistro.numero_sinistro, documentos_dict)
        
        logger.info(f"Sinistro {sinistro.numero_sinistro} sincronizado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar sinistro {sinistro.numero_sinistro}: {str(e)}")
        track_error("erro_sincronizar_legado", e)
        return False
