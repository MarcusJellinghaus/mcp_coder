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
"""

import re

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
