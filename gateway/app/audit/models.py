"""Audit record schema.

One record per gateway request. Records are append-only and never mutated after
creation (see logger.py). Token counts/cost are estimates unless the provider
returns usage — good enough for dashboards and trend analysis.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.compliance.types import ComplianceResult

# Rough heuristic: ~4 characters per token. Replaced by real usage when a
# provider returns it.
_CHARS_PER_TOKEN = 4
# Illustrative blended price per 1K tokens (USD); configurable later.
_USD_PER_1K_TOKENS = 0.0005


def estimate_tokens(*texts: str) -> int:
    return sum(len(t) for t in texts if t) // _CHARS_PER_TOKEN


def estimate_cost(tokens: int) -> float:
    return round(tokens / 1000 * _USD_PER_1K_TOKENS, 6)


@dataclass(slots=True)
class AuditRecord:
    request_id: str
    trace_id: str
    timestamp: str
    endpoint: str
    provider: str
    model: str
    processing_time_ms: float
    pii_count: int
    entity_types: list[str]
    injection_flag: bool
    policy_violations: list[str]
    blocked: bool
    session_id: str
    user_id: str | None = None
    token_count: int = 0
    estimated_cost: float = 0.0
    reason: str | None = None
    entity_types_count: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def build_record(
    *,
    endpoint: str,
    request_id: str,
    trace_id: str,
    session_id: str,
    provider: str,
    model: str,
    processing_time_ms: float,
    result: "ComplianceResult",
    completion_text: str = "",
    prompt_text: str = "",
    user_id: str | None = None,
) -> AuditRecord:
    """Assemble an AuditRecord from a ComplianceResult and timing/usage info."""
    tokens = estimate_tokens(prompt_text, completion_text)
    return AuditRecord(
        request_id=request_id,
        trace_id=trace_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        endpoint=endpoint,
        provider=provider,
        model=model,
        processing_time_ms=round(processing_time_ms, 2),
        pii_count=result.pii_count,
        entity_types=result.entity_types,
        entity_types_count=dict(Counter(e.label for e in result.entities)),
        injection_flag=result.injection_flag,
        policy_violations=result.violations,
        blocked=result.blocked,
        session_id=session_id,
        user_id=user_id,
        token_count=tokens,
        estimated_cost=estimate_cost(tokens),
        reason=result.reason,
    )
