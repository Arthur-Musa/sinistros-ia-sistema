# 🚄 Deploy no Railway - Sistema de Sinistros IA

## 🚀 Deploy Rápido (5 minutos)

### 1. **Preparar Repositório**

```bash
# Inicializar git se ainda não tiver
git init
git add .
git commit -m "Sistema de Sinistros IA pronto para produção"
```

### 2. **Criar Projeto no Railway**

1. Acesse [railway.app](https://railway.app)
2. Clique em "New Project"
3. Escolha "Deploy from GitHub repo"
4. Conecte seu repositório

### 3. **Configurar Serviços**

Railway vai criar automaticamente:

#### **PostgreSQL**
```bash
railway add postgresql
```

#### **Redis**
```bash
railway add redis
```

### 4. **Variáveis de Ambiente**

No dashboard do Railway, adicione:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Geradas automaticamente pelo Railway
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Celery
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/1
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/2

# Segurança
SECRET_KEY=gerar-com-openssl-rand-hex-32
JWT_SECRET_KEY=outra-chave-segura

# Sistema Legado (se tiver)
LEGACY_SYSTEM_URL=https://seu-sistema.com
LEGACY_SYSTEM_API_KEY=sua-api-key
```

### 5. **Deploy Multi-Serviço**

Railway suporta múltiplos serviços no mesmo projeto:

#### **Serviço 1: API Principal**
```yaml
Nome: api
Start Command: bash start.sh
```

#### **Serviço 2: Worker Celery**
```yaml
Nome: worker
Environment: RAILWAY_SERVICE_NAME=worker
Start Command: bash start.sh
```

#### **Serviço 3: Celery Beat**
```yaml
Nome: beat
Environment: RAILWAY_SERVICE_NAME=beat
Start Command: bash start.sh
```

#### **Serviço 4: Dashboard (Opcional)**
```yaml
Nome: dashboard
Build Command: echo "Dashboard estático"
Start Command: python -m http.server $PORT --directory dashboard
```

### 6. **Deploy Automático**

```bash
# Push para GitHub
git push origin main

# Railway faz deploy automático!
```

## 📊 Monitoramento

### **Logs em Tempo Real**
```bash
railway logs
```

### **Métricas**
- CPU, Memória, Rede no dashboard
- Prometheus endpoint: `/metrics`

### **Flower (Celery)**
Adicione como serviço separado:
```yaml
Nome: flower
Environment: RAILWAY_SERVICE_NAME=flower
```

## 🔧 Configurações Avançadas

### **Escalonamento**

```toml
# railway.toml
[deploy]
numReplicas = 2  # Para alta disponibilidade
```

### **Domínio Customizado**

1. No Railway Dashboard → Settings → Domains
2. Adicione seu domínio
3. Configure DNS CNAME

### **Webhooks de Deploy**

Configure no Railway para notificar seu sistema:
```
https://seu-sistema.com/webhook/deploy
```

## 🎯 Endpoints Disponíveis

Após deploy, você terá:

```
# API Principal
https://seu-projeto.railway.app/docs

# Integrações
POST https://seu-projeto.railway.app/api/v1/integrations/legacy/claim
GET  https://seu-projeto.railway.app/api/v1/integrations/claim/{numero}/status

# Health Check
https://seu-projeto.railway.app/health

# Métricas
https://seu-projeto.railway.app/metrics
```

## 🚨 Troubleshooting

### **Erro de Build**
```bash
# Ver logs detalhados
railway logs --service api
```

### **Banco não conecta**
- Verificar DATABASE_URL está correta
- Railway gera automaticamente ao adicionar Postgres

### **Worker não processa**
- Verificar Redis está rodando
- Confirmar CELERY_BROKER_URL

## 💰 Custos Estimados

- **Starter**: $5/mês (inclui $5 de créditos)
- **PostgreSQL**: ~$5-10/mês
- **Redis**: ~$5/mês
- **Workers**: $0.01/GB RAM/hora

Total estimado: ~$20-30/mês para produção básica

## 🎉 Pronto!

Seu sistema está rodando em produção no Railway com:
- ✅ Deploy automático via Git
- ✅ SSL/HTTPS automático
- ✅ Backup automático do banco
- ✅ Monitoramento incluído
- ✅ Escalonamento fácil

Acesse seu dashboard em: `https://railway.app/project/seu-projeto`
