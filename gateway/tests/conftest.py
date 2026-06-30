"""Test configuration.

Pin deterministic settings via environment variables BEFORE any app module
imports (and before get_settings() is first called/cached). os.environ takes
precedence over the developer's local .env, so the suite is independent of
whatever real secrets are in gateway/.env.
"""

import os

os.environ.update(
    {
        "GATEWAY_ENV": "development",
        "AUTH_MODE": "api_key",
        "API_KEYS": "dev-local-key",
        "JWT_SECRET": "test-secret-not-for-prod",
        "DETECTION_ENGINE": "regex",
        "POLICY_FILE": "policies/default.yaml",
        "NEON_DATABASE_URL": "",  # empty -> in-memory repositories
        "VAULT_ENCRYPTION_KEY": "",  # tests that need encryption set their own key
        "REDIS_URL": "redis://localhost:6379/0",
    }
)
