# 🚀 Deploy na Vercel - Sistema de Sinistros IA

## Pré-requisitos
- Conta na [Vercel](https://vercel.com)
- [Vercel CLI](https://vercel.com/cli) instalado (opcional)
- [Git](https://git-scm.com/) instalado

## Passo a Passo

### 1. Instalar a Vercel CLI (opcional, mas recomendado)
```bash
npm install -g vercel
```

### 2. Fazer login na Vercel
```bash
vercel login
```

### 3. Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Banco de Dados
DATABASE_URL=sua_url_do_postgresql

# Redis (para filas)
REDIS_URL=sua_url_do_redis

# Chave da API da OpenAI
OPENAI_API_KEY=sua_chave_da_openai

# Configurações de segurança
SECRET_KEY=uma_chave_secreta_forte
JWT_SECRET_KEY=outra_chave_secreta_forte

# Outras configurações
ENVIRONMENT=production
```

### 4. Fazer o deploy
```bash
# Na raiz do projeto
vercel
```

Siga as instruções no terminal para vincular a um projeto existente ou criar um novo.

### 5. Configurar variáveis de ambiente na Vercel
1. Acesse o [dashboard da Vercel](https://vercel.com/dashboard)
2. Selecione seu projeto
3. Vá em "Settings" > "Environment Variables"
4. Adicione as mesmas variáveis do seu arquivo `.env`

### 6. Configurar Build Settings (se necessário)
A Vercel deve detectar automaticamente as configurações necessárias, mas você pode verificar em:
- Settings > Build & Development Settings

### 7. Acesse seu projeto
Após o deploy, a Vercel fornecerá uma URL como:
```
https://seu-projeto.vercel.app
```

## Endpoints Disponíveis
- API: `https://seu-projeto.vercel.app/api/...`
- Documentação: `https://seu-projeto.vercel.app/docs`
- Health Check: `https://seu-projeto.vercel.app/health`

## Observações Importantes
- A Vercel tem um limite de tempo de execução de 10 segundos para funções serverless no plano gratuito
- Para operações demoradas, considere usar filas (como Celery + Redis)
- Configure domínios personalizados nas configurações do projeto

## Suporte
Em caso de problemas, consulte a [documentação da Vercel](https://vercel.com/docs) ou abra uma issue no repositório.
