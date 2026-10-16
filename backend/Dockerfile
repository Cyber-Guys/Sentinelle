# syntax=docker/dockerfile:1
# Contesto di build: radice del repo (vedi compose.yaml e .dockerignore).
# Nessun pacchetto di sistema: psycopg[binary], numpy e shapely portano le librerie native nelle wheel.
# Le dipendenze sono bloccate in backend/requirements.txt; per aggiornarle:
#   uv pip compile backend/pyproject.toml -o backend/requirements.txt --universal --python-version 3.12 --no-header
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend/src \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY backend/requirements.txt .
RUN --mount=from=ghcr.io/astral-sh/uv:0.11.14,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -r requirements.txt \
    && useradd --system --uid 10001 app \
    && mkdir -p backend/foto && chown app backend/foto

# Stessa struttura del repo: config.py ricava la radice da __file__ (/app).
COPY infra/schema.sql /app/infra/schema.sql
COPY dati /app/dati
COPY scripts/*.py /app/scripts/
COPY backend/config /app/backend/config
COPY backend/src /app/backend/src

USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=60s \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/salute', timeout=2)"
# Un solo worker: la coda degli eventi SSE vive in memoria del processo.
CMD ["uvicorn", "sentinelle.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "2"]
