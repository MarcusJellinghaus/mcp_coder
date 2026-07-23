"""Strict, deterministic parser for the supervisor's machine-readable verdict.

This is the interface between the supervisor session's free text and the review
engine's routing. It is pure (stdlib only, no LLM, no IO). Repair-retries on a
``None`` result are the engine's responsibility (Step 7); this module is
parse-only.
"""

import json
import re
from dataclasses import dataclass, field

_VALID_DECISIONS = frozenset({"dismiss", "tasks", "escalate"})

# Last ```json ... ``` fenced block in the text.
_FENCE_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)

# Fallback: first {...} object in the text.
_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True)
class Verdict:
    """A parsed supervisor decision routing the review loop.

    Attributes:
        decision: One of ``"dismiss"``, ``"tasks"``, or ``"escalate"``.
        tasks: Non-empty, stripped task strings when ``decision == "tasks"``.
        escalate_reason: Optional reason string when ``decision == "escalate"``.
    """

    decision: str
    tasks: list[str] = field(default_factory=list)
    escalate_reason: str | None = None


def parse_verdict(text: str) -> Verdict | None:
    """Extract a fenced JSON verdict from supervisor text.

    Args:
        text: Free-form supervisor output expected to contain a fenced
            ``json`` block with a ``decision`` field.

    Returns:
        A :class:`Verdict` on success, or ``None`` for any malformed or
        invalid input (bad JSON, unknown decision, or a ``tasks`` decision
        without a non-empty task list).
    """
    obj = _extract_object(text)
    if obj is None:
        return None

    decision = obj.get("decision")
    if decision not in _VALID_DECISIONS:
        return None

    if decision == "tasks":
        tasks = _normalize_tasks(obj.get("tasks"))
        if not tasks:
            return None
        return Verdict(decision="tasks", tasks=tasks)

    if decision == "escalate":
        reason = obj.get("escalate_reason")
        escalate_reason = reason if isinstance(reason, str) else None
        return Verdict(decision="escalate", escalate_reason=escalate_reason)

    return Verdict(decision="dismiss")


def _extract_object(text: str) -> dict[str, object] | None:
    """Return the JSON object from the last fenced block, else the first ``{...}``."""
    candidates = _FENCE_RE.findall(text)
    raw = candidates[-1] if candidates else None
    if raw is None:
        match = _OBJECT_RE.search(text)
        raw = match.group(0) if match else None
    if raw is None:
        return None

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(parsed, dict):
        return None
    return parsed


def _normalize_tasks(value: object) -> list[str]:
    """Coerce a raw tasks value into a list of stripped, non-empty strings.

    Args:
        value: A raw value parsed from the verdict JSON, expected to be a list
            of strings but tolerant of any type.

    Returns:
        A list of stripped, non-empty strings, or an empty list when ``value``
        is not a list or contains no usable string entries.
    """
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]
