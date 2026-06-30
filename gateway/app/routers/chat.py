"""POST /v1/chat/completions — provider-agnostic chat with masking + (optional)
streaming-safe rehydration.

Non-streaming:  mask request -> provider.complete -> rehydrate -> JSON.
Streaming:      mask request -> provider.stream -> chunk-safe rehydrate -> SSE.

Either way the user's content is masked before it leaves the gateway, and the
provider's reply is rehydrated before it reaches the client. Streaming uses the
``split_at_last_open`` boundary guard so a placeholder never leaks half-rendered.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.audit.models import build_record
from app.compliance.masker import rehydrate
from app.compliance.streaming import stream_rehydrate
from app.dependencies import audit_dep, engine_dep, provider_dep, vault_dep
from app.observability.metrics import observe_record

if TYPE_CHECKING:
    from app.audit.logger import AuditLogger
    from app.compliance.engine import ComplianceEngine
    from app.compliance.vault import RedisVault
    from app.providers.base import BaseLLMProvider

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    stream: bool = False
    session_id: str | None = None
    user_id: str | None = None


def _blocked_response(result, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "blocked": True,
            "reason": result.reason,
            "violations": result.violations,
            "injectionFlag": result.injection_flag,
            "request_id": request_id,
        },
    )


@router.post("/chat/completions")
async def chat_completions(
    payload: ChatRequest,
    request: Request,
    engine: "ComplianceEngine" = Depends(engine_dep),
    provider: "BaseLLMProvider" = Depends(provider_dep),
    vault: "RedisVault" = Depends(vault_dep),
    audit: "AuditLogger" = Depends(audit_dep),
):
    start = time.perf_counter()
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    trace_id = getattr(request.state, "trace_id", request_id)
    session_id = payload.session_id or trace_id

    def emit(record) -> None:
        audit.log(record)
        observe_record(record)

    # 1. Mask every message; abort if policy blocks any of them.
    masked_parts: list[str] = []
    merged_entities = []
    violations: list[str] = []
    injection = False
    for msg in payload.messages:
        result = await engine.process(msg.content, session_id)
        if result.blocked:
            emit(
                build_record(
                    endpoint="/v1/chat/completions",
                    request_id=request_id,
                    trace_id=trace_id,
                    session_id=session_id,
                    provider=provider.name,
                    model="",
                    processing_time_ms=(time.perf_counter() - start) * 1000,
                    result=result,
                    user_id=payload.user_id,
                )
            )
            return _blocked_response(result, request_id)
        masked_parts.append(f"{msg.role}: {result.masked_text}")
        merged_entities.extend(result.entities)
        violations.extend(result.violations)
        injection = injection or result.injection_flag

    prompt = "\n".join(masked_parts)

    # A merged result for audit (entities/violations across all messages).
    from app.compliance.types import ComplianceResult

    audit_result = ComplianceResult(
        masked_text=prompt,
        entities=merged_entities,
        session_id=session_id,
        violations=violations,
        injection_flag=injection,
        blocked=False,
    )

    # 2a. Streaming response.
    if payload.stream:
        async def event_stream() -> AsyncIterator[bytes]:
            collected: list[str] = []
            async for piece in stream_rehydrate(
                provider.stream(prompt), vault, session_id
            ):
                collected.append(piece)
                data = json.dumps({"choices": [{"delta": {"content": piece}}]})
                yield f"data: {data}\n\n".encode()
            yield b"data: [DONE]\n\n"
            emit(
                build_record(
                    endpoint="/v1/chat/completions",
                    request_id=request_id,
                    trace_id=trace_id,
                    session_id=session_id,
                    provider=provider.name,
                    model="",
                    processing_time_ms=(time.perf_counter() - start) * 1000,
                    result=audit_result,
                    completion_text="".join(collected),
                    prompt_text=prompt,
                    user_id=payload.user_id,
                )
            )

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # 2b. Non-streaming response.
    completion = await provider.complete(prompt)
    final = await rehydrate(completion, vault, session_id)
    emit(
        build_record(
            endpoint="/v1/chat/completions",
            request_id=request_id,
            trace_id=trace_id,
            session_id=session_id,
            provider=provider.name,
            model="",
            processing_time_ms=(time.perf_counter() - start) * 1000,
            result=audit_result,
            completion_text=completion,
            prompt_text=prompt,
            user_id=payload.user_id,
        )
    )
    return JSONResponse(
        content={
            "success": True,
            "choices": [{"message": {"role": "assistant", "content": final}}],
            "maskedPrompt": prompt,
            "piiCount": len(merged_entities),
            "injectionFlag": injection,
            "violations": violations,
            "provider": provider.name,
            "request_id": request_id,
        }
    )
