"""Regex detection engines.

``RegexDetector`` emits a span for every match of each configured pattern.
``ContextGatedRegexDetector`` only emits a match when a context keyword sits
within a character window — essential for noisy patterns (OTP, bank-account
numbers) that would otherwise mask years, quantities, or ZIP codes.

RegexDetector structure adapted from anon_proxy/anon_proxy/regex_detector.py (MIT).
"""

from __future__ import annotations

import re

from app.compliance.types import DetectionSource, PIIEntity


class RegexDetector:
    """Emit PIIEntity spans for each pattern. Insertion order is preserved so
    callers can list most-specific patterns first (a tie-break the overlap
    resolver also enforces by span length)."""

    def __init__(
        self,
        patterns: dict[str, str],
        *,
        source: DetectionSource = DetectionSource.regex,
        flags: int = 0,
        score: float = 1.0,
    ) -> None:
        compiled: list[tuple[str, re.Pattern[str]]] = []
        errors: list[str] = []
        for label, pattern in patterns.items():
            try:
                compiled.append((label, re.compile(pattern, flags)))
            except re.error as exc:
                errors.append(f"  {label!r}: {exc}")
        if errors:
            raise ValueError("invalid regex patterns:\n" + "\n".join(errors))
        self._patterns = compiled
        self._source = source
        self._score = score

    def detect(self, text: str) -> list[PIIEntity]:
        if not self._patterns or not text.strip():
            return []
        out: list[PIIEntity] = []
        for label, rx in self._patterns:
            for m in rx.finditer(text):
                start, end = m.span()
                if start == end:
                    continue
                out.append(
                    PIIEntity(
                        label=label,
                        text=text[start:end],
                        start=start,
                        end=end,
                        score=self._score,
                        source=self._source,
                    )
                )
        return out


class ContextGatedRegexDetector:
    """Emit a match only if one of ``context`` appears within ``window`` chars
    on either side. Keeps high-recall/low-precision patterns from over-masking.
    """

    def __init__(
        self,
        label: str,
        pattern: str,
        context: list[str],
        *,
        window: int = 40,
        score: float = 0.6,
        flags: int = 0,
        source: DetectionSource = DetectionSource.regex,
    ) -> None:
        self._label = label
        self._rx = re.compile(pattern, flags)
        self._context = [c.lower() for c in context]
        self._window = window
        self._score = score
        self._source = source

    def detect(self, text: str) -> list[PIIEntity]:
        if not text.strip():
            return []
        lowered = text.lower()
        out: list[PIIEntity] = []
        for m in self._rx.finditer(text):
            start, end = m.span()
            if start == end:
                continue
            lo = max(0, start - self._window)
            hi = min(len(text), end + self._window)
            ctx = lowered[lo:hi]
            if any(kw in ctx for kw in self._context):
                out.append(
                    PIIEntity(
                        label=self._label,
                        text=text[start:end],
                        start=start,
                        end=end,
                        score=self._score,
                        source=self._source,
                    )
                )
        return out
