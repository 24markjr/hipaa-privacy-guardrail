"""Read + aggregate the append-only audit log for the admin dashboard.

``aggregate`` is a pure function over a list of record dicts so it can be unit
tested without any I/O. ``read_records`` tails the JSONL file (last N lines).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def read_records(path: str, limit: int = 1000) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    out: list[dict] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return round(ordered[k], 2)


def aggregate(records: list[dict]) -> dict:
    total = len(records)
    entity_counts: Counter = Counter()
    violation_counts: Counter = Counter()
    provider_counts: Counter = Counter()
    endpoint_counts: Counter = Counter()

    pii_found = injection = blocked = 0
    tokens = 0
    cost = 0.0
    latencies: list[float] = []

    for r in records:
        pii_found += int(r.get("pii_count", 0))
        injection += 1 if r.get("injection_flag") else 0
        blocked += 1 if r.get("blocked") else 0
        tokens += int(r.get("token_count", 0))
        cost += float(r.get("estimated_cost", 0.0))
        latencies.append(float(r.get("processing_time_ms", 0.0)))
        entity_counts.update(r.get("entity_types_count", {}) or {})
        for v in r.get("policy_violations", []) or []:
            violation_counts[v.split(":", 1)[-1]] += 1
        provider_counts[r.get("provider", "unknown")] += 1
        endpoint_counts[r.get("endpoint", "unknown")] += 1

    avg = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    return {
        "total_requests": total,
        "pii_found": pii_found,
        "injection_attempts": injection,
        "blocked": blocked,
        "token_usage": tokens,
        "estimated_cost": round(cost, 6),
        "entity_types": dict(entity_counts.most_common()),
        "policy_violations": dict(violation_counts.most_common()),
        "provider_usage": dict(provider_counts.most_common()),
        "endpoint_usage": dict(endpoint_counts.most_common()),
        "latency_ms": {
            "avg": avg,
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
        },
    }
