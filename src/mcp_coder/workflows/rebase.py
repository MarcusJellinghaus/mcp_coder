"""Automated ``mcp-coder rebase`` workflow — deterministic shell (Issue #1066).

Python owns the deterministic shell around a single LLM session: pre-flight
guards, the outcome→exit-code decision, the force-push, and a ``finally`` safety
net. This module currently holds only the two pure decision functions; git
helpers, guards, and the orchestrator are added in later steps.

The exit-code contract cross-checks two signals and never trusts either alone:
the LLM's self-reported outcome marker and the actual git repository state (git
is authoritative, worst-case-wins).
"""

import re

_OUTCOME_RE = re.compile(r"^\s*REBASE_OUTCOME:\s*(.+?)\s*$", re.MULTILINE)
_REASON_RE = re.compile(r"^\s*REBASE_REASON:\s*(.+?)\s*$", re.MULTILINE)

_VALID_OUTCOMES = {"success", "aborted"}


def _parse_outcome_marker(response_text: str) -> tuple[str | None, str | None]:
    """Extract ``(outcome, reason)`` from the LLM response.

    ``outcome`` is ``"success"`` | ``"aborted"`` | ``None`` (unparseable or an
    unrecognized value). ``reason`` is the ``REBASE_REASON`` text, or ``None``
    when absent or ``"n/a"``. Last match wins for both markers.
    """
    outcome: str | None = None
    outcome_matches = _OUTCOME_RE.findall(response_text)
    if outcome_matches:
        candidate = outcome_matches[-1].strip().lower()
        if candidate in _VALID_OUTCOMES:
            outcome = candidate

    reason: str | None = None
    reason_matches = _REASON_RE.findall(response_text)
    if reason_matches:
        candidate_reason = reason_matches[-1].strip()
        if candidate_reason and candidate_reason.lower() != "n/a":
            reason = candidate_reason

    return outcome, reason


def _evaluate_pre_push(
    *,
    mid_rebase: bool,
    marker_outcome: str | None,
    rebase_success_shape: bool,
) -> str:
    """Return ``"push"`` or ``"abort"`` (worst-case-wins, git is authoritative)."""
    if mid_rebase:
        return "abort"  # unfinished / crashed session
    if marker_outcome == "aborted":
        return "abort"  # trust the self-report
    if not rebase_success_shape:
        return "abort"  # git can't corroborate success
    return "push"  # marker success/unparseable AND git confirms
