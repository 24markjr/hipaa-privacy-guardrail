"""Prompt-injection detection.

Heuristic, pattern-based flagging of the common injection / jailbreak shapes.
Unlike PII detectors this does not mask — it returns the names of the rules that
fired so the engine can flag (and, per policy, block) the request and record the
violation in the audit log.

This is intentionally conservative (high precision); it is a tripwire, not a
substitute for provider-side safety.
"""

from __future__ import annotations

import re

# rule name -> pattern (case-insensitive)
INJECTION_RULES: dict[str, str] = {
    "ignore_previous": r"ignore\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above)\s+(?:instructions|prompts?|messages?)",
    "disregard_instructions": r"disregard\s+(?:all\s+)?(?:previous|prior|the)\s+(?:instructions|rules)",
    "reveal_system_prompt": r"(?:reveal|show|print|repeat|disclose|leak)\s+(?:me\s+)?(?:your\s+)?(?:the\s+)?(?:system\s+prompt|initial\s+instructions|developer\s+message)",
    "developer_mode": r"\b(?:developer|dev|debug)\s+mode\b",
    "jailbreak_dan": r"\b(?:jailbreak|DAN\s+mode|do\s+anything\s+now)\b",
    "override_role": r"you\s+are\s+now\s+(?:a|an|in)\b|from\s+now\s+on\s+you\s+(?:are|will)",
    "exfiltrate_rules": r"(?:what\s+are|tell\s+me)\s+your\s+(?:rules|instructions|guidelines|constraints)",
}


class InjectionDetector:
    def __init__(self, rules: dict[str, str] | None = None) -> None:
        self._rules = [
            (name, re.compile(pat, re.IGNORECASE))
            for name, pat in (rules or INJECTION_RULES).items()
        ]

    def detect(self, text: str) -> list[str]:
        """Return the names of every injection rule that matched."""
        if not text.strip():
            return []
        return [name for name, rx in self._rules if rx.search(text)]
