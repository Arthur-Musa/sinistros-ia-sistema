# 🤖 Como Usar o Sistema de Agentes de Sinistros

## 📋 O que são os Agentes?

O sistema possui 5 agentes de IA especializados que trabalham juntos para analisar sinistros:

1. **📋 Agente de Triagem**: Classifica o tipo de sinistro e define prioridade
2. **🔍 Agente de Análise**: Verifica documentação e valida informações
3. **💰 Agente de Cálculo**: Calcula o valor da indenização baseado na apólice
4. **⚖️ Agente de Compliance**: Verifica se tudo está conforme as regulamentações
5. **👔 Gerente de Sinistros**: Coordena todos os agentes e toma a decisão final

## 🚀 Como Usar - Passo a Passo

### 1️⃣ Configure a Chave da OpenAI
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e adicione sua chave
OPENAI_API_KEY=sua-chave-aqui
```

### 2️⃣ Inicie a API
```bash
# Ative o ambiente virtual
source venv/bin/activate

# Inicie o servidor da API
python src/api/main.py
```

### 3️⃣ Use os Agentes de 3 Formas:

#### Opção A: Exemplo Completo Automático
```bash
# Execute o exemplo que criei para você
python exemplo_uso_completo.py
```

#### Opção B: Via Dashboard Visual
1. Abra o dashboard em outro terminal:
   ```bash
   cd dashboard
   python3 -m http.server 8080
   ```
2. Acesse http://localhost:8080
3. Use o botão "+" para criar sinistros
4. Os agentes analisarão automaticamente

#### Opção C: Via API Diretamente
```python
import requests

# 1. Criar sinistro
sinistro = {
    "data_ocorrencia": "2024-01-15",
    "segurado_nome": "João Silva",
    "segurado_documento": "123.456.789-00",
    "segurado_telefone": "(11) 98765-4321",
    "apolice_numero": "APL-2024-001",
    "descricao": "Colisão frontal...",
    "documentos": ["boletim.pdf"],
    "valor_estimado": 15000.00
}

# Envia para API
response = requests.post("http://localhost:8000/sinistros", json=sinistro)
numero = response.json()["numero_sinistro"]

# 2. Solicitar análise dos agentes
requests.post(f"http://localhost:8000/sinistros/{numero}/analisar")

# 3. Aguardar e ver resultado
# Os agentes trabalharão em conjunto para analisar
```

## 🔄 Fluxo de Trabalho dos Agentes

```
Sinistro Criado
      ↓
[Gerente de Sinistros] - Coordena todo processo
      ↓
[Agente Triagem] - Classifica tipo e urgência
      ↓
[Agente Análise] - Verifica documentos
      ↓
[Agente Cálculo] - Calcula indenização
      ↓
[Agente Compliance] - Verifica conformidade
      ↓
[Gerente de Sinistros] - Decisão final
      ↓
Resultado: Aprovado/Negado com justificativas
```

## 📊 O que os Agentes Analisam?

- **Tipo de sinistro**: Auto, residencial, vida, etc.
- **Documentação**: Se está completa e válida
- **Valor**: Se está dentro dos limites da apólice
- **Fraude**: Indicadores de possível fraude
- **Compliance**: Conformidade com regulamentações
- **Urgência**: Prioridade do atendimento

## 💡 Exemplo de Resultado

Após análise, você receberá:
```json
{
  "decisao": "APROVADO",
  "valor_aprovado": 12500.00,
  "justificativas": [
    "Documentação completa e válida",
    "Valor dentro dos limites da apólice",
    "Sem indicadores de fraude"
  ],
  "agente_usado": "GerenteSinistros",
  "compliance_ok": true
}
```

## ❓ Perguntas Frequentes

**P: Preciso chamar cada agente individualmente?**
R: Não! O Gerente de Sinistros coordena todos automaticamente.

**P: Quanto tempo leva a análise?**
R: Geralmente 5-10 segundos, dependendo da complexidade.

**P: Posso testar sem a chave da OpenAI?**
R: A API funcionará, mas a análise dos agentes retornará erro.

**P: Os agentes aprendem com o tempo?**
R: Cada análise é independente, mas você pode ajustar as instruções dos agentes.

## 🎯 Teste Agora!

1. Execute: `python exemplo_uso_completo.py`
2. Veja os agentes trabalhando em tempo real
3. Receba a análise completa com justificativas

É isso! Os agentes fazem todo trabalho pesado de análise para você! 🚀
