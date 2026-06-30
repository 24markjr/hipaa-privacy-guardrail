# Multi-stage build. The default image ships the regex engine only (small).
# Build with --build-arg INSTALL_PRESIDIO=1 to bake in Presidio + spaCy.
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
ARG INSTALL_PRESIDIO=0
RUN pip install --upgrade pip && \
    pip install . && \
    if [ "$INSTALL_PRESIDIO" = "1" ]; then \
        pip install ".[presidio]" && python -m spacy download en_core_web_lg ; \
    fi

COPY . .

EXPOSE 8000
# Render (and similar platforms) inject $PORT; fall back to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
