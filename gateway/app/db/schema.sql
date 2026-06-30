-- Neon / Postgres schema. Applied idempotently on startup.
-- NOTE: this database is intentionally PHI-free. Analyses store de-identified
-- metadata and the *masked* summary only — never the original note, the
-- restored summary, or the token->PHI mapping (those live in the Redis vault
-- with a TTL).

CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name          TEXT NOT NULL DEFAULT '',
    role          TEXT NOT NULL DEFAULT 'doctor',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analyses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id      TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    provider        TEXT NOT NULL,
    pii_count       INTEGER NOT NULL DEFAULT 0,
    entity_types    TEXT[] NOT NULL DEFAULT '{}',
    injection_flag  BOOLEAN NOT NULL DEFAULT false,
    blocked         BOOLEAN NOT NULL DEFAULT false,
    processing_ms   DOUBLE PRECISION NOT NULL DEFAULT 0,
    masked_summary  TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analyses_user_created
    ON analyses (user_id, created_at DESC);
