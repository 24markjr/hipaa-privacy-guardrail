"""Policy Engine — configurable compliance rules (no hardcoded behaviour).

A policy is a YAML profile (see gateway/policies/*.yaml, adapted from cloakpipe's
TOML profiles). It maps entity labels to actions and decides what to do with a
detected injection attempt. Swapping ``POLICY_FILE`` changes gateway behaviour
without touching code.

Decision precedence for an entity label:
    explicit by_label override  >  default action
A label listed in ``disabled`` is treated as ``allow`` (not acted on).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.compliance.types import Action, Decision

# gateway/ root (…/gateway/app/compliance/policy.py -> parents[2] == gateway/)
_GATEWAY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class Policy:
    name: str
    profile: str
    default_action: Action
    by_label: dict[str, Action] = field(default_factory=dict)
    disabled: set[str] = field(default_factory=set)
    injection_action: Action = Action.allow  # allow == "flag only"
    retention_days: int = 90

    def decide(self, label: str) -> Decision:
        up = label.upper()
        if up in self.disabled:
            return Decision(Action.allow, rule=f"{up}:disabled")
        if up in self.by_label:
            return Decision(self.by_label[up], rule=up)
        return Decision(self.default_action, rule="default")


def _coerce_action(value: str, *, allow_flag: bool = False) -> Action:
    v = str(value).strip().lower()
    if allow_flag and v == "flag":
        return Action.allow
    return Action(v)


def load_policy(policy_file: str) -> Policy:
    path = Path(policy_file)
    if not path.is_absolute():
        path = _GATEWAY_ROOT / policy_file
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    actions = data.get("actions", {})
    by_label = {
        k.upper(): _coerce_action(v) for k, v in (actions.get("by_label") or {}).items()
    }
    return Policy(
        name=data.get("name", path.stem),
        profile=data.get("profile", "general"),
        default_action=_coerce_action(actions.get("default", "mask")),
        by_label=by_label,
        disabled={s.upper() for s in (data.get("disabled") or [])},
        injection_action=_coerce_action(
            (data.get("injection") or {}).get("action", "flag"), allow_flag=True
        ),
        retention_days=int((data.get("audit") or {}).get("retention_days", 90)),
    )
