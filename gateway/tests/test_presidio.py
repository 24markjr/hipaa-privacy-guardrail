"""Phase 5 — Presidio recognizer specs (always) + live engine (if installed).

The spec tests need no Presidio install; the integration test is skipped unless
``presidio_analyzer`` and a spaCy model are available.
"""

from __future__ import annotations

import re

import pytest

from app.compliance.detectors.presidio_engine import (
    CUSTOM_ENTITIES,
    RECOGNIZER_SPECS,
)


def test_specs_cover_required_indian_entities():
    required = {"IN_GSTIN", "IN_PAN", "IN_AADHAAR", "IN_IFSC", "IN_UPI", "IN_OTP", "IN_BANK_ACCOUNT"}
    assert required.issubset(set(CUSTOM_ENTITIES))


def test_spec_regexes_compile_and_match():
    # The Indian regexes are reused from the regex engine — sanity check a few.
    by_entity = {s.entity: s for s in RECOGNIZER_SPECS}
    pan = by_entity["IN_PAN"].patterns[0][1]
    assert re.search(pan, "ABCDE1234F")
    gstin = by_entity["IN_GSTIN"].patterns[0][1]
    assert re.search(gstin, "22ABCDE1234F1Z5")


def test_otp_spec_has_low_base_score_and_context():
    otp = next(s for s in RECOGNIZER_SPECS if s.entity == "IN_OTP")
    assert otp.patterns[0][2] <= 0.3  # low base score -> needs context boost
    assert "otp" in otp.context


@pytest.mark.integration
def test_presidio_engine_detects_person_and_pan():
    pytest.importorskip("presidio_analyzer")
    import spacy  # noqa: F401

    try:
        from app.compliance.detectors.presidio_engine import PresidioDetector

        det = PresidioDetector(model_name="en_core_web_sm", score_threshold=0.4)
    except Exception as exc:  # spaCy model not downloaded
        pytest.skip(f"presidio/spaCy model unavailable: {exc}")

    ents = det.detect("Patient John Smith, PAN ABCDE1234F, came in today.")
    labels = {e.label for e in ents}
    assert "IN_PAN" in labels
    assert "PERSON" in labels  # NER — the thing regex cannot do
