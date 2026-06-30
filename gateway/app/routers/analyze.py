"""Clinical-note analysis + detect-only scan + metadata.

  POST /v1/analyze        — JSON { note, provider?, policy? }
  POST /v1/analyze/file   — multipart upload (PDF / DOCX / TXT) + provider?/policy? form fields
  POST /v1/scan           — detect-only (no LLM); powers the playgrounds
  GET  /v1/meta           — available providers + policy profiles (for UI selectors)

Analyze pipeline: detect+mask (Compliance Engine) -> LLM -> rehydrate. A policy
block (Aadhaar, prompt injection, …) returns 422 and never reaches the provider.
Per-request ``provider`` and ``policy`` are selectable (the gateway is not
hardcoded to one of either).
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.audit.models import build_record
from app.compliance.masker import rehydrate
from app.config import Settings
from app.db.models import AnalysisRecord
from app.dependencies import (
    audit_dep,
    engine_dep,
    history_sink_dep,
    policies_dep,
    provider_dep,
    providers_dep,
    settings_dep,
    vault_dep,
)
from app.ingest.extract import ExtractionError, UnsupportedFileType, extract_text
from app.observability.metrics import observe_record

if TYPE_CHECKING:
    from app.audit.logger import AuditLogger
    from app.compliance.engine import ComplianceEngine
    from app.compliance.vault import RedisVault
    from app.history.sink import HistorySink
    from app.providers.base import BaseLLMProvider

router = APIRouter(prefix="/v1", tags=["analyze"])

_DISCLAIMER = (
    "AI-generated for clinician review only — not a diagnosis or a substitute "
    "for professional medical judgment."
)

# Two-section prompt: a summary plus suggestions for the treating physician.
_CLINICAL_PROMPT = """You are an experienced clinical AI assistant.

The following clinical note has already been de-identified for compliance.
Use ONLY the information present. Do not invent facts.

Return your answer in EXACTLY these two sections, with these literal headers:

===SUMMARY===
A concise clinical summary: main symptoms, likely diagnosis, current
treatments/medications, and recommended follow-up.

===SUGGESTIONS===
Considerations for the treating physician: differentials worth ruling out, gaps
in the workup, monitoring to consider, and documentation completeness. Frame as
suggestions for review, not directives.

Clinical Note:

{text}
"""

_SUGGESTIONS_MARKER = "===SUGGESTIONS==="
_SUMMARY_MARKER = "===SUMMARY==="


def _split_sections(text: str) -> tuple[str, str]:
    """Split the model output into (summary, suggestions)."""
    body = text.replace(_SUMMARY_MARKER, "").strip()
    if _SUGGESTIONS_MARKER in body:
        summary, suggestions = body.split(_SUGGESTIONS_MARKER, 1)
        return summary.strip(), suggestions.strip()
    return body, ""


def _resolve_provider(name: str | None, providers: dict, default: "BaseLLMProvider"):
    return providers.get(name, default) if name else default


class AnalyzeRequest(BaseModel):
    note: str = Field(..., min_length=1)
    session_id: str | None = None
    user_id: str | None = None
    provider: str | None = None
    policy: str | None = None


class ScanRequest(BaseModel):
    text: str = Field(..., min_length=1)
    policy: str | None = None
    session_id: str | None = None


async def _run_analysis(
    *,
    note: str,
    source: str,
    request: Request,
    engine: "ComplianceEngine",
    provider: "BaseLLMProvider",
    policy_name: str | None,
    policies: dict,
    vault: "RedisVault",
    audit: "AuditLogger",
    history: "HistorySink",
    session_id: str | None,
    payload_user_id: str | None,
) -> JSONResponse:
    t0 = time.perf_counter()
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    trace_id = getattr(request.state, "trace_id", request_id)
    user_id = getattr(request.state, "user_id", None) or payload_user_id
    session_id = session_id or trace_id
    policy = policies.get(policy_name) if policy_name else None

    t_comp = time.perf_counter()
    result = await engine.process(note, session_id, policy=policy)
    compliance_ms = (time.perf_counter() - t_comp) * 1000

    def _audit(masked_summary: str, prompt: str, total_ms: float) -> None:
        record = build_record(
            endpoint="/v1/analyze",
            request_id=request_id,
            trace_id=trace_id,
            session_id=session_id,
            provider=provider.name,
            model="",
            processing_time_ms=total_ms,
            result=result,
            completion_text=masked_summary,
            prompt_text=prompt,
            user_id=user_id,
        )
        audit.log(record)
        observe_record(record)
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
                    processing_ms=round(total_ms, 2),
                    masked_summary=masked_summary,
                )
            )

    if result.blocked:
        _audit("", "", (time.perf_counter() - t0) * 1000)
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "blocked": True,
                "reason": result.reason,
                "violations": result.violations,
                "injectionFlag": result.injection_flag,
                "policy": policy.name if policy else None,
            },
        )

    t_llm = time.perf_counter()
    raw = await provider.complete(_CLINICAL_PROMPT.format(text=result.masked_text))
    provider_ms = (time.perf_counter() - t_llm) * 1000

    masked_summary, masked_suggestions = _split_sections(raw)

    t_rehy = time.perf_counter()
    final_summary = await rehydrate(masked_summary, vault, session_id)
    final_suggestions = await rehydrate(masked_suggestions, vault, session_id)
    rehydrate_ms = (time.perf_counter() - t_rehy) * 1000

    total_ms = (time.perf_counter() - t0) * 1000
    _audit(masked_summary, result.masked_text, total_ms)

    return JSONResponse(
        content={
            "success": True,
            "source": source,
            "originalText": note,
            "maskedText": result.masked_text,
            "piiCount": result.pii_count,
            "entityTypes": result.entity_types,
            "finalSummary": final_summary,
            "suggestions": final_suggestions,
            "disclaimer": _DISCLAIMER,
            "violations": result.violations,
            "injectionFlag": result.injection_flag,
            "provider": provider.name,
            "policy": policy.name if policy else None,
            "timings": {
                "compliance_ms": round(compliance_ms, 1),
                "provider_ms": round(provider_ms, 1),
                "rehydrate_ms": round(rehydrate_ms, 1),
                "total_ms": round(total_ms, 1),
            },
        }
    )


@router.post("/analyze")
async def analyze(
    payload: AnalyzeRequest,
    request: Request,
    engine: "ComplianceEngine" = Depends(engine_dep),
    default_provider: "BaseLLMProvider" = Depends(provider_dep),
    providers: dict = Depends(providers_dep),
    policies: dict = Depends(policies_dep),
    vault: "RedisVault" = Depends(vault_dep),
    audit: "AuditLogger" = Depends(audit_dep),
    history: "HistorySink" = Depends(history_sink_dep),
) -> JSONResponse:
    return await _run_analysis(
        note=payload.note,
        source="text",
        request=request,
        engine=engine,
        provider=_resolve_provider(payload.provider, providers, default_provider),
        policy_name=payload.policy,
        policies=policies,
        vault=vault,
        audit=audit,
        history=history,
        session_id=payload.session_id,
        payload_user_id=payload.user_id,
    )


@router.post("/analyze/file")
async def analyze_file(
    request: Request,
    file: UploadFile = File(...),
    provider: str | None = Form(None),
    policy: str | None = Form(None),
    engine: "ComplianceEngine" = Depends(engine_dep),
    default_provider: "BaseLLMProvider" = Depends(provider_dep),
    providers: dict = Depends(providers_dep),
    policies: dict = Depends(policies_dep),
    vault: "RedisVault" = Depends(vault_dep),
    audit: "AuditLogger" = Depends(audit_dep),
    history: "HistorySink" = Depends(history_sink_dep),
) -> JSONResponse:
    content = await file.read()
    try:
        note = extract_text(file.filename or "upload", content)
    except UnsupportedFileType as exc:
        return JSONResponse(status_code=415, content={"success": False, "detail": str(exc)})
    except ExtractionError as exc:
        return JSONResponse(status_code=422, content={"success": False, "detail": str(exc)})

    return await _run_analysis(
        note=note,
        source=f"file:{file.filename}",
        request=request,
        engine=engine,
        provider=_resolve_provider(provider, providers, default_provider),
        policy_name=policy,
        policies=policies,
        vault=vault,
        audit=audit,
        history=history,
        session_id=None,
        payload_user_id=None,
    )


@router.post("/scan")
async def scan(
    payload: ScanRequest,
    request: Request,
    engine: "ComplianceEngine" = Depends(engine_dep),
    policies: dict = Depends(policies_dep),
) -> dict:
    """Detect-only: run the compliance engine WITHOUT calling an LLM.

    Powers the prompt-injection and secret-detection playgrounds — shows what is
    detected/masked/blocked, proving nothing sensitive would reach a provider.
    """
    session_id = payload.session_id or getattr(request.state, "trace_id", "scan")
    policy = policies.get(payload.policy) if payload.policy else None
    result = await engine.process(payload.text, session_id, policy=policy)
    return {
        "blocked": result.blocked,
        "reason": result.reason,
        "violations": result.violations,
        "injectionFlag": result.injection_flag,
        "piiCount": result.pii_count,
        "entityTypes": result.entity_types,
        "maskedText": result.masked_text,
        "policy": policy.name if policy else None,
    }


@router.get("/meta")
async def meta(
    providers: dict = Depends(providers_dep),
    policies: dict = Depends(policies_dep),
    settings: Settings = Depends(settings_dep),
) -> dict:
    return {
        "providers": sorted(providers.keys()),
        "policies": sorted(policies.keys()),
        "default_provider": settings.llm_provider.value,
        "default_policy": next(
            (p.name for p in policies.values() if str(settings.policy_file).endswith(p.name + ".yaml")),
            None,
        ),
    }
