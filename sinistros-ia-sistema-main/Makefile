.PHONY: help install run test deploy clean

help:
	@echo "Comandos disponíveis:"
	@echo "  make install    - Instalar dependências"
	@echo "  make run        - Executar localmente"
	@echo "  make test       - Executar testes"
	@echo "  make deploy     - Deploy para Railway"
	@echo "  make clean      - Limpar arquivos temporários"

install:
	pip install -r requirements.txt

run:
	python src/api/main.py

test:
	pytest tests/ -v

deploy:
	railway up

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
