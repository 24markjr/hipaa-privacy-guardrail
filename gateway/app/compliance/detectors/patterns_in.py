"""PII patterns with most-specific-first ordering.

Ordering matters (a point reinforced in review): structurally distinct,
high-confidence patterns must be considered before generic ones so we don't,
for example, mask a PAN-shaped substring that is really part of a GSTIN.

Two safeguards work together:
  1. Declaration order here lists the most specific patterns first.
  2. ``resolve_overlaps`` (longest-span-wins) is the safety net — GSTIN (15
     chars) beats the embedded PAN (10 chars) even if both fire.

Aadhaar/PAN regexes are ported from cloakpipe/detector/patterns.rs (MIT);
GSTIN/UPI/IFSC/bank-account/OTP are added here (not present in cloakpipe).
"""

from __future__ import annotations

from app.compliance.detectors.base import Detector
from app.compliance.detectors.regex_engine import (
    ContextGatedRegexDetector,
    RegexDetector,
)

# --- Specific, high-confidence patterns (most specific first) --------------
# GSTIN: 2 state digits + PAN(10) + entity-no(1) + 'Z' + checksum(1) = 15 chars.
SPECIFIC_PATTERNS: dict[str, str] = {
    "IN_GSTIN": r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b",
    "IN_PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    # Aadhaar never starts with 0 or 1; allow optional spaces between groups.
    "IN_AADHAAR": r"\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b",
    "IN_IFSC": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
    "US_SSN": r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",
}

# --- General patterns -------------------------------------------------------
# EMAIL is declared before UPI so a real email wins; UPI uses a negative
# lookahead so it never matches the local@domain portion of an email.
GENERAL_PATTERNS: dict[str, str] = {
    "EMAIL_ADDRESS": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "IN_UPI": r"\b[A-Za-z0-9.\-_]{2,}@[A-Za-z]{2,}(?![\w.])",
    "IP_ADDRESS": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\b",
    "PHONE_NUMBER": r"(?:\+[1-9][0-9]{0,2}[-.\s]?)?\(?[0-9]{2,4}\)?[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{4}",
    "DATE_OF_BIRTH": r"\b[0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4}\b",
}


def build_pii_detectors() -> list[Detector]:
    """Detector list in precedence order. Context-gated detectors (OTP,
    bank-account) come last; the overlap resolver settles any real conflict."""
    return [
        RegexDetector(SPECIFIC_PATTERNS),
        RegexDetector(GENERAL_PATTERNS),
        # OTP: a bare 4-6 digit run only counts as PII near OTP context words.
        ContextGatedRegexDetector(
            "IN_OTP",
            r"\b[0-9]{4,6}\b",
            context=["otp", "one time password", "one-time password", "verification", "code", "passcode"],
        ),
        # Indian bank account numbers: 9-18 digits, only near account context.
        ContextGatedRegexDetector(
            "IN_BANK_ACCOUNT",
            r"\b[0-9]{9,18}\b",
            context=["account", "a/c", "acct", "account no", "account number", "bank"],
            score=0.7,
        ),
    ]
