"""Phase 8 — non-blocking, append-only audit logger."""

from __future__ import annotations

import asyncio
import json

from app.audit.logger import AuditLogger
from app.audit.models import AuditRecord, build_record
from app.compliance.types import ComplianceResult, DetectionSource, PIIEntity


def _record(i: int) -> AuditRecord:
    return AuditRecord(
        request_id=f"r{i}",
        trace_id=f"t{i}",
        timestamp="2026-01-01T00:00:00Z",
        endpoint="/v1/analyze",
        provider="echo",
        model="m",
        processing_time_ms=1.0,
        pii_count=0,
        entity_types=[],
        injection_flag=False,
        policy_violations=[],
        blocked=False,
        session_id="s",
    )


async def test_logger_writes_jsonl(tmp_path):
    path = tmp_path / "audit.jsonl"
    logger = AuditLogger(str(path))
    await logger.start()
    for i in range(5):
        logger.log(_record(i))
    await asyncio.wait_for(logger._queue.join(), timeout=5)
    await logger.stop()

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5
    assert json.loads(lines[0])["request_id"] == "r0"


async def test_log_never_blocks_and_drops_when_full():
    # No worker started: queue fills, extra records are dropped (counted), not raised.
    logger = AuditLogger("unused.jsonl", maxsize=2)
    for i in range(5):
        logger.log(_record(i))  # must not raise
    assert logger.dropped == 3


def test_build_record_estimates_tokens_and_counts_entities():
    result = ComplianceResult(
        masked_text="<EMAIL_ADDRESS_1>",
        entities=[
            PIIEntity("EMAIL_ADDRESS", "a@b.com", 0, 7, 1.0, DetectionSource.regex),
            PIIEntity("EMAIL_ADDRESS", "c@d.com", 8, 15, 1.0, DetectionSource.regex),
            PIIEntity("IN_PAN", "ABCDE1234F", 16, 26, 1.0, DetectionSource.regex),
        ],
        session_id="s",
    )
    rec = build_record(
        endpoint="/v1/chat/completions",
        request_id="r",
        trace_id="t",
        session_id="s",
        provider="gemini",
        model="gemini-2.5-flash",
        processing_time_ms=12.3,
        result=result,
        completion_text="hello world",
        prompt_text="some masked prompt",
    )
    assert rec.pii_count == 3
    assert rec.entity_types_count == {"EMAIL_ADDRESS": 2, "IN_PAN": 1}
    assert rec.token_count > 0
    assert rec.estimated_cost >= 0
