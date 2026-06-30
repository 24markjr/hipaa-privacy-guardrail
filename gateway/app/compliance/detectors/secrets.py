"""Secret detection — API keys, tokens, cloud credentials, private keys.

Patterns ported from cloakpipe/detector/patterns.rs (secrets block) (MIT),
with private-key blocks and password assignments added.

Secrets are high-precision and must be caught before anything reaches an LLM,
so they get score 1.0 and source=secret.
"""

from __future__ import annotations

import re

from app.compliance.detectors.regex_engine import RegexDetector
from app.compliance.types import DetectionSource

# Single-line patterns.
SECRET_PATTERNS: dict[str, str] = {
    "AWS_ACCESS_KEY": r"AKIA[0-9A-Z]{16}",
    "API_KEY_PREFIXED": r"sk-(?:proj|live|test|prod)-[A-Za-z0-9]{10,}",
    "API_KEY_GENERIC": r"sk-[A-Za-z0-9]{32,}",
    "GITHUB_TOKEN": r"(?:gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,})",
    "JWT_TOKEN": r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    "CONNECTION_STRING": r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^\s]+",
    "PASSWORD_ASSIGNMENT": r"(?i)(?:password|passwd|pwd)\s*[:=]\s*\S+",
}

# Multi-line: capture the whole PEM block (PRIVATE KEY / SSH key).
PRIVATE_KEY_PATTERN = {
    "PRIVATE_KEY": r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
}


def build_secret_detectors() -> list:
    return [
        RegexDetector(SECRET_PATTERNS, source=DetectionSource.secret),
        RegexDetector(
            PRIVATE_KEY_PATTERN, source=DetectionSource.secret, flags=re.DOTALL
        ),
    ]
