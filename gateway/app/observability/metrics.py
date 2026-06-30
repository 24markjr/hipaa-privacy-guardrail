"""Prometheus metrics.

The HTTP-level latency histogram (giving P50/P90/P95/P99 via histogram_quantile)
and request counts come from prometheus-fastapi-instrumentator. On top of that we
register *domain* metrics the gateway cares about — PII detected, injection
attempts, policy violations, tokens, processing time, blocked requests — and
update them from a single ``observe_record`` call driven by the audit record, so
metrics and audit never drift apart.

All metrics use the default registry, which the instrumentator also exposes at
``/metrics`` — so one scrape endpoint covers everything.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from prometheus_client import Counter, Gauge, Histogram

if TYPE_CHECKING:
    from app.audit.models import AuditRecord

REQUESTS = Counter(
    "gateway_requests_total",
    "Compliance-processed requests.",
    ["endpoint", "provider", "outcome"],
)
BLOCKED = Counter("gateway_blocked_total", "Requests blocked by policy/injection.", ["endpoint"])
PII_DETECTED = Counter("gateway_pii_detected_total", "PII entities detected.", ["entity_type"])
INJECTION_ATTEMPTS = Counter("gateway_injection_attempts_total", "Prompt-injection attempts flagged.")
POLICY_VIOLATIONS = Counter("gateway_policy_violations_total", "Policy violations.", ["rule"])
TOKENS = Counter("gateway_tokens_total", "Estimated tokens processed.", ["provider"])
ACTIVE_REQUESTS = Gauge("gateway_active_requests", "In-flight requests.")
PROCESSING_SECONDS = Histogram(
    "gateway_processing_seconds",
    "Compliance+provider processing time.",
    ["endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


def observe_record(record: "AuditRecord") -> None:
    """Update domain metrics from a completed audit record."""
    outcome = "blocked" if record.blocked else "ok"
    REQUESTS.labels(record.endpoint, record.provider, outcome).inc()
    if record.blocked:
        BLOCKED.labels(record.endpoint).inc()
    for entity_type, count in record.entity_types_count.items():
        PII_DETECTED.labels(entity_type).inc(count)
    if record.injection_flag:
        INJECTION_ATTEMPTS.inc()
    for violation in record.policy_violations:
        # "policy:IN_AADHAAR" / "injection:ignore_previous" -> bounded label set
        rule = violation.split(":", 1)[-1]
        POLICY_VIOLATIONS.labels(rule).inc()
    if record.token_count:
        TOKENS.labels(record.provider).inc(record.token_count)
    PROCESSING_SECONDS.labels(record.endpoint).observe(record.processing_time_ms / 1000.0)
