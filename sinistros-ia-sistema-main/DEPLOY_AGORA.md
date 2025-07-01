# 🚀 Deploy Imediato no Railway

Seu projeto está pronto! Siga estes passos:

## 1. **Criar Conta no Railway (2 min)**
👉 [railway.app/login](https://railway.app/login)
- Login com GitHub (recomendado)
- Ou criar conta com email

## 2. **Criar Novo Projeto (1 min)**
```
Dashboard → New Project → Deploy from GitHub repo
```
- Autorize o Railway acessar seu GitHub
- Selecione o repositório `sinistros-ia-sistema`

## 3. **Adicionar Serviços (3 min)**

### PostgreSQL
```
+ New → Database → PostgreSQL
```

### Redis
```
+ New → Database → Redis
```

## 4. **Configurar Variáveis (2 min)**

No painel do projeto → Variables → RAW Editor:

```env
OPENAI_API_KEY=cole-sua-chave-openai-aqui
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/1
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/2
SECRET_KEY=railway-gera-automaticamente
ENVIRONMENT=production
```

## 5. **Deploy! (automático)**

Assim que configurar as variáveis, Railway inicia o deploy automaticamente!

## 6. **Adicionar Workers (opcional)**

Para processamento assíncrono completo:

### Worker Celery
```
+ New → Empty Service
Nome: worker
Variables: RAILWAY_SERVICE_NAME=worker
```

### Celery Beat
```
+ New → Empty Service  
Nome: beat
Variables: RAILWAY_SERVICE_NAME=beat
```

## 🎯 Pronto em 10 minutos!

Seu sistema estará disponível em:
```
https://sinistros-ia-sistema-production.up.railway.app
```

### Testar:
```bash
# Health check
curl https://seu-app.railway.app/health

# Documentação
https://seu-app.railway.app/docs
```

## 📱 Próximos Passos

1. **Domínio customizado**: Settings → Domains
2. **Monitoramento**: Observability → Logs
3. **Escalar**: Settings → Replicas

---

💡 **Dica**: Railway tem $5 grátis/mês no plano Starter!
