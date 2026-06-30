# Deployment Runbook — AI Privacy & Compliance Gateway

Stack: **Gateway** (FastAPI on Render) · **Redis** (Upstash) · **Postgres** (Neon) · **Frontend** (Vercel, after P3).

---

## 1. Upstash Redis (you still need to create this)
1. https://console.upstash.com → Create Database → Redis → region **Singapore (ap-southeast-1)** (match Neon/Render).
2. Copy the **`rediss://` connection URL** (TLS). That's your `REDIS_URL`.

## 2. Neon (done)
Connection string already provided. Rend
er uses it as `NEON_DATABASE_URL`.
The gateway auto-creates the `users` + `analyses` tables on first boot.

## 3. Render (Blueprint)
1. Push this repo to GitHub.
2. Render → **New → Blueprint** → select the repo. It reads `render.yaml` and creates the `ai-privacy-gateway` web service.
3. Open the service → **Environment** tab → set the five secret vars below.
4. Deploy. Health check is `/health`.

> Free plan note: Render disks need the **Starter** plan. On Free, remove the
> `disk:` block from `render.yaml` — audit JSONL becomes ephemeral (fine; the
> durable per-doctor history lives in Neon).

## 4. Paste these into Render → Environment

> Copy the exact values from your local `gateway/.env` — do **not** hardcode real secrets in this committed file.

| Key | Value (source) |
|-----|----------------|
| `NEON_DATABASE_URL` | your Neon pooled connection string |
| `REDIS_URL` | Upstash TLS URL: `rediss://default:<password>@<host>.upstash.io:6379` |
| `GEMINI_API_KEY` | your Google Gemini API key |
| `JWT_SECRET` | the generated secret in `gateway/.env` |
| `API_KEYS` | your chosen admin/dashboard key |

The non-secret vars (`GATEWAY_ENV`, `AUTH_MODE`, `DETECTION_ENGINE`, `POLICY_FILE`,
`AUDIT_LOG_PATH`) are already baked into `render.yaml`.

## 5. Verify after deploy
```
curl https://<your-service>.onrender.com/health      # {"status":"ok",...}
curl https://<your-service>.onrender.com/ready       # {"ready":true,"checks":{"redis":"ok"}}
```
Dashboard: `https://<your-service>.onrender.com/dashboard` (enter your `API_KEYS` value).
Metrics:   `https://<your-service>.onrender.com/metrics`

## 6. Frontend (Vercel) — after P3 build
The new frontend will read the gateway URL from `VITE_API_URL`. In Vercel →
Project → Settings → Environment Variables:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://<your-service>.onrender.com` |

## 7. ⚠️ Rotate exposed secrets
The Neon password and Gemini key were shared in chat. After deploy works:
- **Neon:** reset the `neondb_owner` password, update `NEON_DATABASE_URL` in Render + local `.env`.
- **Gemini:** regenerate the API key, update `GEMINI_API_KEY` in Render + local `.env`.
