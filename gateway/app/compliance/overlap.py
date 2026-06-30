"""Overlap resolution for detected spans.

adapted from anon_proxy/anon_proxy/masker.py (_resolve_overlaps) (MIT)

When several detectors fire on overlapping regions (e.g. a GSTIN contains a
PAN-shaped substring), we must keep a non-overlapping subset. Selection is
longest-span-first, then highest score, then leftmost, then label — so the more
specific match (GSTIN, 15 chars) always beats the embedded PAN (10 chars).
Spans that merely touch at a boundary do not count as overlapping.
"""

from __future__ import annotations

from app.compliance.types import PIIEntity


def resolve_overlaps(entities: list[PIIEntity]) -> list[PIIEntity]:
    if not entities:
        return []
    candidates = sorted(
        entities,
        key=lambda e: (-(e.end - e.start), -e.score, e.start, e.label),
    )
    kept: list[PIIEntity] = []
    for e in candidates:
        if any(e.start < k.end and e.end > k.start for k in kept):
            continue
        kept.append(e)
    return sorted(kept, key=lambda e: e.start)
