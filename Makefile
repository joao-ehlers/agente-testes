PY ?= .venv/bin/python

.PHONY: instalar imagens testes exemplo exemplo-docker api avaliar avaliar-llm
instalar:
	python3 -m venv .venv && .venv/bin/pip install -e '.[avaliacao]'

imagens:
	docker build -t agente-testes-runner-python:latest -f docker/runner-python.Dockerfile docker

testes:
	$(PY) -m pytest -q

exemplo:
	AGENTE_LLM=nenhum $(PY) -m agente_testes.cli executar exemplos/loja/loja.py --raiz exemplos/loja \
	  --requisitos exemplos/loja/requisitos.yaml --executor local --saida-md relatorio-exemplo.md --nao-falhar

exemplo-docker: imagens
	AGENTE_LLM=nenhum $(PY) -m agente_testes.cli executar exemplos/loja/loja.py --raiz exemplos/loja \
	  --requisitos exemplos/loja/requisitos.yaml --executor docker --saida-md relatorio-exemplo.md --nao-falhar

api:
	$(PY) -m uvicorn agente_testes.api.app:app --reload --port 8000

# Entrega 2: casos controlados, métricas, gráficos e evidências em entrega2/resultados
avaliar: imagens
	$(PY) -m agente_testes.cli avaliar --executor docker --repeticoes 5

# mesma bancada usando o LLM configurado (GEMINI_API_KEY)
avaliar-llm: imagens
	$(PY) -m agente_testes.cli avaliar --modo llm --executor docker --repeticoes 3 --saida entrega2/resultados-llm
