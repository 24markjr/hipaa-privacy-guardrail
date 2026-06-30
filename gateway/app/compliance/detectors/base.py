"""Detector protocol.

Every detection backend — regex, context-gated regex, Presidio (Phase 5) —
implements this one method, so the engine can mix and swap them freely.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.compliance.types import PIIEntity


@runtime_checkable
class Detector(Protocol):
    def detect(self, text: str) -> list[PIIEntity]: ...
