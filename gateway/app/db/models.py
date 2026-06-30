"""Persistence domain models (DB-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class User:
    id: str
    email: str
    password_hash: str
    name: str = ""
    role: str = "doctor"
    created_at: datetime | None = None

    def public(self) -> dict:
        """Serialisable view without the password hash."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass(slots=True)
class AnalysisRecord:
    """A PHI-free record of one analysis, for the doctor's history view."""

    user_id: str
    request_id: str
    endpoint: str
    provider: str
    pii_count: int = 0
    entity_types: list[str] = field(default_factory=list)
    injection_flag: bool = False
    blocked: bool = False
    processing_ms: float = 0.0
    masked_summary: str = ""  # de-identified summary only — never raw PHI
    created_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "provider": self.provider,
            "pii_count": self.pii_count,
            "entity_types": self.entity_types,
            "injection_flag": self.injection_flag,
            "blocked": self.blocked,
            "processing_ms": self.processing_ms,
            "masked_summary": self.masked_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
