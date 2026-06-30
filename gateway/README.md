# AI Privacy & Compliance Gateway

Production-grade privacy/compliance middleware that sits between any client
application and any LLM provider. Detects and masks sensitive data (PII, secrets,
Indian financial identifiers), enforces configurable compliance policies, and
restores originals after the model responds — with streaming support,
observability, and immutable audit logging.

> Status: under active construction. Phase 0–1 (async FastAPI core + middleware)
> are in place. See the repository root for the full phased plan.

## Quick start (dev)

```bash
cd gateway
cp .env.example .env          # adjust as needed
pip install .                 # add ".[presidio]" for the Presidio engine
uvicorn app.main:app --reload
```

Then:

```bash
curl localhost:8000/health
curl localhost:8000/ready     # checks Redis connectivity
```

## Full stack (one command)

From the repository root:

```bash
docker compose up --build
```

Brings up gateway + Redis + Prometheus + Grafana:

| Service | URL |
|---------|-----|
| Gateway API / docs | http://localhost:8000/docs |
| Admin dashboard | http://localhost:8000/dashboard (enter API key `dev-local-key`) |
| Prometheus metrics | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana (anon viewer) | http://localhost:3000 |

## Architecture (target)

```
Client → FastAPI Gateway
  → [request-context → access-log → auth] middleware
  → Compliance Engine (injection → detect → policy → vault-tokenize)
  → Provider Router (Gemini / OpenAI / Claude / Ollama)
  → Guardrails → Rehydration → response
  → (off the hot path) immutable audit + Prometheus metrics
```

See [`CREDITS.md`](CREDITS.md) for third-party attributions.
