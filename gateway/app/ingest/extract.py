"""Plain-text extraction from PDF / DOCX / TXT uploads."""

from __future__ import annotations

import io

# 5 MB cap — clinical notes are small; this guards against abuse / OOM.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
SUPPORTED_EXTENSIONS = ("pdf", "docx", "txt", "md")


class UnsupportedFileType(ValueError):
    """File extension/type we don't extract text from."""


class ExtractionError(ValueError):
    """The file matched a supported type but text extraction failed."""


def _ext(filename: str) -> str:
    return filename.lower().rsplit(".", 1)[-1] if "." in filename else ""


def _from_pdf(content: bytes) -> str:
    import fitz  # PyMuPDF

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"could not read PDF: {exc}") from exc
    try:
        return "\n".join(page.get_text() for page in doc).strip()
    finally:
        doc.close()


def _from_docx(content: bytes) -> str:
    from docx import Document

    try:
        document = Document(io.BytesIO(content))
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"could not read Word document: {exc}") from exc
    return "\n".join(p.text for p in document.paragraphs).strip()


def extract_text(filename: str, content: bytes) -> str:
    """Return plain text from a supported document.

    Raises UnsupportedFileType for unknown extensions, ExtractionError on a
    parse failure or empty result.
    """
    if len(content) > MAX_UPLOAD_BYTES:
        raise ExtractionError(
            f"file too large ({len(content)} bytes); max {MAX_UPLOAD_BYTES}"
        )

    ext = _ext(filename)
    if ext == "pdf":
        text = _from_pdf(content)
    elif ext == "docx":
        text = _from_docx(content)
    elif ext in ("txt", "md"):
        text = content.decode("utf-8", errors="replace").strip()
    else:
        raise UnsupportedFileType(
            f"unsupported file type '.{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    if not text.strip():
        raise ExtractionError("no extractable text found (is this a scanned image?)")
    return text
