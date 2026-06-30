"""POST /v1/analyze — the MVP clinical-summary flow, ported onto the gateway.

Pipeline:  detect+mask (Compliance Engine) -> LLM (provider) -> rehydrate.
If the policy blocks the request (e.g. Aadhaar present, or prompt injection),
nothing is sent to the provider and a 422 explains why.

This preserves the original product behaviour while routing it through the new
async compliance pipeline.
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.audit.models import build_record
from app.compliance.masker import rehydrate
from app.db.models import AnalysisRecord
from app.dependencies import (
    audit_dep,
    engine_dep,
    history_sink_dep,
    provider_dep,
    vault_dep,
)
from app.observability.metrics import observe_record

if TYPE_CHECKING:
    from app.audit.logger import AuditLogger
    from app.compliance.engine import ComplianceEngine
    from app.compliance.vault import RedisVault
    from app.history.sink import HistorySink
    from app.providers.base import BaseLLMProvider

router = APIRouter(prefix="/v1", tags=["analyze"])

# Ported verbatim from the MVP's aiService prompt.
_CLINICAL_PROMPT = """You are an experienced clinical AI assistant.

The following clinical note has already been de-identified for HIPAA compliance.

Your task is to:
1. Produce a concise clinical summary.
2. Mention the patient's main symptoms.
3. Mention likely diagnosis.
4. Mention treatments or medications.
5. Mention recommended follow-up.

Do NOT invent facts. Use only the information present.

Clinical Note:

{text}
"""


class AnalyzeRequest(BaseModel):
    note: str = Field(..., min_length=1)
    session_id: str | None = None
    user_id: str | None = None


@router.post("/analyze")
async def analyze(
    payload: AnalyzeRequest,
    request: Request,
    engine: "ComplianceEngine" = Depends(engine_dep),
    provider: "BaseLLMProvider" = Depends(provider_dep),
    vault: "RedisVault" = Depends(vault_dep),
    audit: "AuditLogger" = Depends(audit_dep),
    history: "HistorySink" = Depends(history_sink_dep),
) -> JSONResponse:
    start = time.perf_counter()
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    trace_id = getattr(request.state, "trace_id", request_id)
    # Authenticated doctor (JWT) — used for per-user history.
    user_id = getattr(request.state, "user_id", None) or payload.user_id
    session_id = payload.session_id or trace_id

    result = await engine.process(payload.note, session_id)

    def _audit(completion: str = "", masked_summary: str = "", prompt: str = "") -> None:
        elapsed_ms = (time.perf_counter() - start) * 1000
        record = build_record(
            endpoint="/v1/analyze",
            request_id=request_id,
            trace_id=trace_id,
            session_id=session_id,
            provider=provider.name,
            model="",
            processing_time_ms=elapsed_ms,
            result=result,
            completion_text=completion,
            prompt_text=prompt,
            user_id=user_id,
        )
        audit.log(record)
        observe_record(record)
        # Per-doctor history (PHI-free): only when a doctor is authenticated.
        if user_id:
            history.log(
                AnalysisRecord(
                    user_id=user_id,
                    request_id=request_id,
                    endpoint="/v1/analyze",
                    provider=provider.name,
                    pii_count=result.pii_count,
                    entity_types=result.entity_types,
                    injection_flag=result.injection_flag,
                    blocked=result.blocked,
                    processing_ms=round(elapsed_ms, 2),
                    masked_summary=masked_summary,
                )
            )

    if result.blocked:
        _audit()
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "blocked": True,
                "reason": result.reason,
                "violations": result.violations,
                "injectionFlag": result.injection_flag,
            },
        )

    # Let each provider use its own configured default model.
    ai_summary = await provider.complete(_CLINICAL_PROMPT.format(text=result.masked_text))
    final_summary = await rehydrate(ai_summary, vault, session_id)
    # ai_summary is the de-identified (still-masked) summary — safe to persist.
    _audit(completion=ai_summary, masked_summary=ai_summary, prompt=result.masked_text)

    return JSONResponse(
        content={
            "success": True,
            "originalText": payload.note,
            "maskedText": result.masked_text,
            "piiCount": result.pii_count,
            "entityTypes": result.entity_types,
            "aiSummary": ai_summary,
            "finalSummary": final_summary,
            "violations": result.violations,
            "injectionFlag": result.injection_flag,
            "provider": provider.name,
        }
    )
