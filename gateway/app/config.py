"""Typed application settings.

A single ``Settings`` object is loaded once at startup and injected everywhere
via dependency injection (see ``app/dependencies.py``). No module should read
``os.environ`` directly — go through ``get_settings()`` so configuration stays
testable and centralised.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class DetectionEngine(str, Enum):
    regex = "regex"
    presidio = "presidio"


class LLMProvider(str, Enum):
    gemini = "gemini"
    openai = "openai"
    claude = "claude"
    ollama = "ollama"


class AuthMode(str, Enum):
    api_key = "api_key"
    jwt = "jwt"
    none = "none"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- App ----
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8000
    gateway_env: str = "development"
    log_level: str = "INFO"

    # ---- Detection ----
    detection_engine: DetectionEngine = DetectionEngine.regex
    presidio_spacy_model: str = "en_core_web_lg"
    presidio_score_threshold: float = 0.5

    # ---- Policy ----
    policy_file: str = "policies/default.yaml"

    # ---- Provider ----
    llm_provider: LLMProvider = LLMProvider.gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # ---- Redis vault ----
    redis_url: str = "redis://localhost:6379/0"
    vault_ttl_seconds: int = 3600
    vault_token_style: str = "placeholder"  # placeholder | format_preserving
    vault_encryption_key: str | None = None  # Fernet key; enables encrypt-at-rest

    # ---- CORS ----
    # Comma-separated allowed origins for the browser frontend. "*" allows any
    # (safe here because auth uses Bearer/X-API-Key headers, not cookies).
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])

    # ---- Auth ----
    auth_mode: AuthMode = AuthMode.api_key
    # NoDecode: take the raw env string and split it ourselves (below) instead of
    # letting pydantic-settings JSON-decode it.
    api_keys: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["dev-local-key"])
    jwt_secret: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720  # 12h

    # ---- Database (Neon / Postgres) ----
    # If unset, the gateway falls back to in-memory repositories (dev/tests).
    neon_database_url: str | None = None

    # ---- Audit ----
    audit_log_path: str = "./data/audit.jsonl"
    audit_queue_maxsize: int = 10_000

    # ---- Upstream HTTP ----
    upstream_timeout_seconds: float = 120.0
    upstream_max_retries: int = 3

    @field_validator("api_keys", "cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        """Accept a comma-separated string from the env and split into a list."""
        if isinstance(v, str):
            return [k.strip() for k in v.split(",") if k.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.gateway_env.lower() == "production"

    def validate_for_runtime(self) -> None:
        """Fail fast on insecure production configuration."""
        if self.is_production and self.jwt_secret == "dev-insecure-secret-change-me":
            raise RuntimeError(
                "JWT_SECRET must be set to a strong secret in production "
                "(currently the insecure development default)."
            )
        if self.is_production and not self.vault_encryption_key:
            raise RuntimeError(
                "VAULT_ENCRYPTION_KEY must be set in production so PHI is "
                "encrypted at rest in Redis. Generate one with: "
                "python -c \"from cryptography.fernet import Fernet; "
                'print(Fernet.generate_key().decode())"'
            )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton (cached)."""
    return Settings()
