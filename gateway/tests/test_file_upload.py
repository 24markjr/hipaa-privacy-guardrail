"""File upload — text extraction (PDF/DOCX/TXT) + /v1/analyze/file endpoint."""

from __future__ import annotations

import io

import fakeredis.aioredis
import httpx
import pytest

from app.compliance.detectors.injection import InjectionDetector
from app.compliance.detectors.patterns_in import build_pii_detectors
from app.compliance.detectors.secrets import build_secret_detectors
from app.compliance.engine import ComplianceEngine
from app.compliance.policy import Policy
from app.compliance.types import Action
from app.compliance.vault import RedisVault
from app.dependencies import audit_dep, engine_dep, history_sink_dep, provider_dep, vault_dep
from app.ingest.extract import ExtractionError, UnsupportedFileType, extract_text
from app.main import create_app
from app.providers.base import BaseLLMProvider


# ---- extraction ----
def test_extract_txt():
    assert "hello world" in extract_text("note.txt", b"hello world")


def test_extract_docx_roundtrip():
    from docx import Document

    doc = Document()
    doc.add_paragraph("Patient John Doe, MRN12345")
    buf = io.BytesIO()
    doc.save(buf)
    text = extract_text("note.docx", buf.getvalue())
    assert "John Doe" in text and "MRN12345" in text


def test_extract_pdf_roundtrip():
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Patient Jane Roe email jane@clinic.com")
    data = doc.tobytes()
    doc.close()
    text = extract_text("note.pdf", data)
    assert "Jane Roe" in text


def test_extract_unsupported():
    with pytest.raises(UnsupportedFileType):
        extract_text("scan.png", b"\x89PNG...")


def test_extract_empty_pdf_raises():
    import fitz

    doc = fitz.open()
    doc.new_page()  # blank page, no text
    data = doc.tobytes()
    doc.close()
    with pytest.raises(ExtractionError):
        extract_text("blank.pdf", data)


# ---- endpoint ----
class EchoProvider(BaseLLMProvider):
    name = "echo"

    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        return prompt.split("Clinical Note:\n\n", 1)[-1].strip()


class _FakeSink:
    def log(self, record) -> None:  # noqa: D401
        pass


@pytest.fixture
async def client():
    app = create_app()
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    vault = RedisVault(redis, ttl_seconds=60)
    engine = ComplianceEngine(
        build_secret_detectors() + build_pii_detectors(),
        InjectionDetector(),
        Policy(name="t", profile="g", default_action=Action.mask),
        vault,
    )
    app.dependency_overrides[vault_dep] = lambda: vault
    app.dependency_overrides[provider_dep] = lambda: EchoProvider()
    app.dependency_overrides[engine_dep] = lambda: engine
    app.dependency_overrides[audit_dep] = lambda: _FakeSink()
    app.dependency_overrides[history_sink_dep] = lambda: _FakeSink()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers={"X-API-Key": "dev-local-key"}
    ) as c:
        yield c
    await redis.aclose()


async def test_analyze_file_masks_and_rehydrates(client):
    resp = await client.post(
        "/v1/analyze/file",
        files={"file": ("note.txt", b"Patient email jane@clinic.com", "text/plain")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "jane@clinic.com" not in body["maskedText"]      # masked outbound
    assert "jane@clinic.com" in body["finalSummary"]        # restored inbound
    assert body["source"].startswith("file:")


async def test_analyze_file_unsupported_type(client):
    resp = await client.post(
        "/v1/analyze/file",
        files={"file": ("scan.png", b"\x89PNG\r\n", "image/png")},
    )
    assert resp.status_code == 415
