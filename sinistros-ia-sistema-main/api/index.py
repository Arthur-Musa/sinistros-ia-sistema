from src.api.main_production import app

# Este arquivo é necessário para o deploy na Vercel
# A Vercel espera encontrar um arquivo `api/index.py` como ponto de entrada

# O objeto `app` é importado do seu arquivo principal
# A Vercel usará este objeto para rotear as requisições HTTP
