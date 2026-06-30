"""Core data contracts shared across the Compliance Engine.

These three types are the universal currency of the pipeline:

    detectors  ──▶ PIIEntity        (what was found, and where)
    policy     ──▶ Decision         (what to do about each entity)
    engine     ──▶ ComplianceResult (the masked outcome the router acts on)

Keeping them dependency-free (pure dataclasses/enums) lets every other module
import them without creating import cycles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DetectionSource(str, Enum):
    """Which detector produced an entity (useful for telemetry & debugging)."""

    regex = "regex"
    presidio = "presidio"
    secret = "secret"
    injection = "injection"


@dataclass(frozen=True, slots=True)
class PIIEntity:
    """A single detected sensitive span.

    Shape adapted from anon_proxy's PIIEntity (MIT). ``start``/``end`` are
    character offsets into the *original* text; ``score`` is the detector's
    confidence in [0, 1].
    """

    label: str
    text: str
    start: int
    end: int
    score: float = 1.0
    source: DetectionSource = DetectionSource.regex

    @property
    def length(self) -> int:
        return self.end - self.start


class Action(str, Enum):
    """What the Policy Engine decides to do with an entity (or the request)."""

    allow = "allow"
    mask = "mask"
    block = "block"


@dataclass(frozen=True, slots=True)
class Decision:
    """A policy decision attached to an entity."""

    action: Action
    rule: str  # the policy rule that produced this decision (for audit)


@dataclass(slots=True)
class ComplianceResult:
    """The outcome of running text through the Compliance Engine.

    The router inspects ``blocked`` first; if False it forwards ``masked_text``
    to the provider and later rehydrates the reply using ``session_id``.
    """

    masked_text: str
    entities: list[PIIEntity] = field(default_factory=list)
    session_id: str = ""
    violations: list[str] = field(default_factory=list)
    injection_flag: bool = False
    blocked: bool = False
    reason: str | None = None

    @property
    def pii_count(self) -> int:
        return len(self.entities)

    @property
    def entity_types(self) -> list[str]:
        return sorted({e.label for e in self.entities})
