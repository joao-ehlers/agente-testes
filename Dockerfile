# Imagem do próprio Agente de Testes (API REST).
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends docker.io && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md ./
COPY agente_testes ./agente_testes
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["uvicorn", "agente_testes.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
