"""Pure, deterministic parser for the highest severity in a reviewer report.

This is the deterministic **backstop** primitive consumed by the Step 5 severity
transform: it reports the highest ``critical|high|medium|low`` token present in a
reviewer report. It is pure (stdlib only, no LLM, no IO) — the sibling of
``verdict.py``.

The reviewer contract is ``file:line — SEVERITY — desc``. The SEVERITY token is
matched **only in its anchored position** between the two separators of a finding
line, never free-scanned across the whole report: a severity word in a finding's
description text (e.g. a ``low`` finding described as "high coupling") or in a
summary line (e.g. "No critical/high findings") must not raise the detected
ceiling.

The deterministic **backstop transform** :func:`_apply_severity_floor` — the sole
consumer of :func:`max_severity` — lives here too: it rewrites a low-severity
``tasks`` verdict to ``dismiss`` at/after the lane's ``strict_from_round`` so the
loop stops burning rounds on nitpicks (Step 5).
"""

import logging
import re

from .config import ReviewConfig
from .verdict import Verdict

logger = logging.getLogger(__name__)

_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}

# Anchor on the finding-line format ``file:line — SEVERITY — desc``, tolerating the
# formatting a fresh reviewer LLM may emit (see prompts.md:342-343): the separator
# may be an em-dash ``—`` OR one-or-more ASCII hyphens ``-``, and the SEVERITY token
# (like the backticked ``file:line``) may be wrapped in backticks. The token must
# still sit BETWEEN the two separators, so a severity word in a description or
# summary line does not count. (``-`` is first in the class so it is a literal, not
# a range.)
_RE = re.compile(
    r"[-—]+\s*`?(critical|high|medium|low)`?\s*[-—]+",
    re.IGNORECASE,
)


def max_severity(report: str) -> str | None:
    """Return the highest severity token in a reviewer report, or None.

    Args:
        report: Free-form reviewer output whose findings follow the
            ``file:line — SEVERITY — desc`` contract.

    Returns:
        One of ``"critical"``, ``"high"``, ``"medium"``, ``"low"`` — the highest
        severity present in an anchored finding line — or ``None`` when no
        severity token appears (the fail-open signal consumed by the Step 5
        backstop).
    """
    best: str | None = None
    best_rank = 0
    for match in _RE.finditer(report):
        token = match.group(1).lower()
        rank = _RANK[token]
        if rank > best_rank:
            best, best_rank = token, rank
    return best


def _apply_severity_floor(
    verdict: Verdict,
    report: str,
    round_number: int,
    config: ReviewConfig,
    pending_ci_note: str | None,
) -> Verdict:
    """Downgrade a low-severity ``tasks`` verdict to ``dismiss`` at the floor.

    The deterministic backstop for the advisory severity prompt rule: from
    ``config.strict_from_round`` onward, a ``tasks`` verdict whose reviewer
    report carries no ``critical``/``high`` finding is rewritten to
    ``Verdict("dismiss")`` so the loop stops burning rounds on nitpicks. Two
    guards keep it conservative: it **fails open** (leaves the verdict
    unchanged) on an unparseable report, and it is **skipped entirely** while a
    CI finding is pending — red CI is a must-fix, exempt from the floor.

    Args:
        verdict: The freshly parsed supervisor verdict.
        report: The fresh reviewer report (not the supervisor text) whose
            anchored finding lines carry the severities.
        round_number: The current 1-based round number.
        config: The review workflow config (supplies ``strict_from_round``).
        pending_ci_note: The carried CI-as-finding note, or ``None``. When set,
            the round is exempt and never downgraded.

    Returns:
        ``Verdict("dismiss")`` when the floor applies, else ``verdict``
        unchanged.
    """
    if verdict.decision != "tasks":
        return verdict
    if pending_ci_note is not None:
        return verdict
    if round_number < config.strict_from_round:
        return verdict
    top = max_severity(report)
    if top is None:
        return verdict
    if top in ("critical", "high"):
        return verdict
    logger.info(
        "Round %d: severity floor: downgrading tasks -> dismiss (max=%s)",
        round_number,
        top,
    )
    return Verdict(decision="dismiss")
