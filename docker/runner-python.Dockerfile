# Imagem descartável onde os testes gerados são executados (Filtro 5).
FROM python:3.12-slim
RUN pip install --no-cache-dir "pytest>=8" "pytest-cov>=5" "coverage>=7" "httpx>=0.27" "pytest-timeout>=2.2" \
    && useradd -m -u 1000 runner
WORKDIR /workspace
USER runner
