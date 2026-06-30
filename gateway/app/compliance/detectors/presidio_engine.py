"""Microsoft Presidio detection engine (config-switchable alternative to regex).

Selected via ``DETECTION_ENGINE=presidio``. Adds real NER (PERSON, etc. — the
thing regex can't do) plus custom pattern recognizers for the Indian entities,
reusing the *same* regex strings as the regex engine so the two stay in sync.

Two design points that matter:
  * Presidio + spaCy is CPU-heavy and synchronous, so the engine runs
    ``detect`` off the event loop (ComplianceEngine sets offload_detection=True
    for this engine). ``detect`` itself stays a plain sync method.
  * OTP / bank-account patterns are low base-score and rely on Presidio's
    context enhancement + a score threshold to gate them — the same
    false-positive guard the regex engine gets from ContextGatedRegexDetector.

The recognizer *specs* are plain data (no Presidio import), so they can be
unit-tested even where Presidio isn't installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.compliance.detectors.patterns_in import GENERAL_PATTERNS, SPECIFIC_PATTERNS
from app.compliance.types import DetectionSource, PIIEntity

# Built-in Presidio entities we keep (NER + common PII). Secrets are handled by
# the separate regex secret detectors, so they're not requested here.
DEFAULT_BUILTIN_ENTITIES: list[str] = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IP_ADDRESS",
    "US_SSN",
    "CREDIT_CARD",
    "LOCATION",
]


@dataclass(frozen=True, slots=True)
class RecognizerSpec:
    """A custom Presidio PatternRecognizer, expressed as plain data."""

    entity: str
    patterns: list[tuple[str, str, float]]  # (name, regex, score)
    context: list[str] = field(default_factory=list)


# Reuse the canonical regexes (single source of truth with the regex engine).
RECOGNIZER_SPECS: list[RecognizerSpec] = [
    RecognizerSpec("IN_GSTIN", [("gstin", SPECIFIC_PATTERNS["IN_GSTIN"], 0.9)], ["gst", "gstin"]),
    RecognizerSpec("IN_PAN", [("pan", SPECIFIC_PATTERNS["IN_PAN"], 0.85)], ["pan", "income tax"]),
    RecognizerSpec(
        "IN_AADHAAR", [("aadhaar", SPECIFIC_PATTERNS["IN_AADHAAR"], 0.85)], ["aadhaar", "uidai"]
    ),
    RecognizerSpec("IN_IFSC", [("ifsc", SPECIFIC_PATTERNS["IN_IFSC"], 0.9)], ["ifsc", "bank", "branch"]),
    RecognizerSpec("IN_UPI", [("upi", GENERAL_PATTERNS["IN_UPI"], 0.6)], ["upi", "vpa", "pay"]),
    # Low base score: only survives the threshold when context boosts it.
    RecognizerSpec(
        "IN_OTP",
        [("otp", r"\b[0-9]{4,6}\b", 0.3)],
        ["otp", "one time password", "verification", "code", "passcode"],
    ),
    RecognizerSpec(
        "IN_BANK_ACCOUNT",
        [("bank_acct", r"\b[0-9]{9,18}\b", 0.3)],
        ["account", "a/c", "acct", "bank"],
    ),
]

CUSTOM_ENTITIES: list[str] = [s.entity for s in RECOGNIZER_SPECS]


class PresidioDetector:
    """Wraps a Presidio ``AnalyzerEngine`` behind the ``Detector`` protocol."""

    def __init__(
        self,
        model_name: str = "en_core_web_lg",
        score_threshold: float = 0.5,
        entities: list[str] | None = None,
    ) -> None:
        # Imports are local so this module can be imported (for the specs) even
        # when Presidio isn't installed.
        from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        nlp_engine = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": model_name}],
            }
        ).create_engine()

        analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
        for spec in RECOGNIZER_SPECS:
            analyzer.registry.add_recognizer(
                PatternRecognizer(
                    supported_entity=spec.entity,
                    patterns=[Pattern(name=n, regex=r, score=s) for n, r, s in spec.patterns],
                    context=spec.context,
                )
            )

        self._analyzer = analyzer
        self._threshold = score_threshold
        self._entities = (entities or DEFAULT_BUILTIN_ENTITIES) + CUSTOM_ENTITIES

    def detect(self, text: str) -> list[PIIEntity]:
        if not text.strip():
            return []
        results = self._analyzer.analyze(
            text=text,
            language="en",
            entities=self._entities,
            score_threshold=self._threshold,
        )
        return [
            PIIEntity(
                label=r.entity_type,
                text=text[r.start : r.end],
                start=r.start,
                end=r.end,
                score=r.score,
                source=DetectionSource.presidio,
            )
            for r in results
        ]


def build_presidio_detectors(
    model_name: str = "en_core_web_lg", score_threshold: float = 0.5
) -> list:
    return [PresidioDetector(model_name=model_name, score_threshold=score_threshold)]
