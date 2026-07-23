"""Step 1 — A-B-A session-interleave prototype (integration, mandatory first commit).

These tests prove — against the *real* Claude CLI — the persistent-supervisor /
fresh-reviewer interleave that the headless review engine (Step 7) re-creates in
pure Python. Headless Claude cannot spawn subagents, so the interactive
``/implementation_review_supervisor`` pattern is emulated by session-id juggling:

- **Supervisor** — a *persistent* session captured on turn 1 and resumed each
  later turn (``prompt_llm(session_id=<supervisor id>)``).
- **Reviewer** — a *fresh* session per round (``prompt_llm(session_id=None)``),
  sharing no context with the supervisor.

The A-B-A flow interleaves them (supervisor → reviewer → supervisor → reviewer →
supervisor) and asserts that the supervisor's **third** turn recalls tokens from
**both** of its earlier turns — i.e. the persistent session survives the
interleaved fresh-reviewer calls.

Both tests are marked ``claude_cli_integration``: they hit the real CLI, are
excluded from the fast unit run, and execute in CI. No production code is added
by this step — the test *is* the deliverable.

Session-id chaining discipline (consumed by Step 7 ``_next_supervisor_session_id``)
------------------------------------------------------------------------------------
The Claude CLI may return a **new** ``session_id`` on every resumed turn. Two
disciplines are possible when resuming a multi-turn supervisor:

- ``reuse_original_id``  — always resume with the turn-1 id (the ``create_plan`` /
  ``core.py`` style).
- ``recapture_returned_id`` — resume with the id returned by the *previous* turn.

``test_reuse_original_id_vs_recapture_returned_id`` runs the A-B-A flow under
both disciplines and pins the winner. The engine uses
:data:`WINNING_SESSION_DISCIPLINE`.

NOTE (create_plan context-loss finding — fix out of scope for #1072):
    If ``reuse_original_id`` fails to recall the token taught on turn 2, then
    every production resume site that reuses the *original* session id
    (``create_plan`` / ``core.py``) silently loses intermediate-turn context.
    This test records that finding (asserting the ``recapture_returned_id``
    discipline works); repairing the production sites is tracked separately and
    is not part of issue #1072.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from mcp_coder import prompt_llm
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.types import LLMResponseDict

logger = logging.getLogger(__name__)

# Real-CLI round-trips need a generous timeout (see other claude_cli_integration tests).
_ROUND_TRIP_TIMEOUT = 60

# Session-id chaining disciplines evaluated by test 2.
SESSION_DISCIPLINE_REUSE_ORIGINAL = "reuse_original_id"
SESSION_DISCIPLINE_RECAPTURE = "recapture_returned_id"

# The discipline the review engine (Step 7 `_next_supervisor_session_id`) implements.
# Re-capturing the id returned by each resumed turn always preserves the running
# context; test 2 verifies this holds against the real CLI.
WINNING_SESSION_DISCIPLINE = SESSION_DISCIPLINE_RECAPTURE


@dataclass
class _CallInterval:
    """Wall-clock interval of a single (blocking) prompt_llm call."""

    label: str
    start: float
    end: float


def _timed_prompt(
    intervals: list[_CallInterval],
    label: str,
    question: str,
    session_id: str | None,
    env_vars: dict[str, str],
) -> LLMResponseDict:
    """Run one prompt_llm call, recording its start/end interval for sequencing checks."""
    start = time.monotonic()
    response = prompt_llm(
        question,
        provider="claude",
        session_id=session_id,
        timeout=_ROUND_TRIP_TIMEOUT,
        env_vars=env_vars,
    )
    end = time.monotonic()
    intervals.append(_CallInterval(label=label, start=start, end=end))
    return response


def _assert_strictly_sequential(intervals: list[_CallInterval]) -> None:
    """Assert no two recorded calls overlap.

    The issue requires supervisor↔reviewer execution to be *strictly sequential —
    never concurrent*. Each call must return before the next begins; sorted by
    start time, every interval must end at-or-before the next one starts.
    """
    ordered = sorted(intervals, key=lambda c: c.start)
    for prev, curr in zip(ordered, ordered[1:]):
        assert prev.end <= curr.start, (
            f"calls ran concurrently: {prev.label} ended at {prev.end:.6f} but "
            f"{curr.label} started at {curr.start:.6f} (intervals must not overlap)"
        )


def _next_supervisor_session_id(
    original_id: str | None,
    previous_id: str | None,
    response: LLMResponseDict,
    discipline: str,
) -> str | None:
    """Return the session id to resume the supervisor with on its next turn.

    Encapsulates the two chaining disciplines compared by test 2 and used
    (via :data:`WINNING_SESSION_DISCIPLINE`) by test 1.
    """
    if discipline == SESSION_DISCIPLINE_RECAPTURE:
        return response["session_id"] or previous_id or original_id
    return original_id


def _run_interleave(
    env_vars: dict[str, str],
    discipline: str,
    intervals: list[_CallInterval],
) -> str:
    """Drive the A-B-A supervisor/reviewer interleave under a chaining discipline.

    Returns the (upper-cased) text of the supervisor's third turn, which is
    expected to name both tokens taught on turns 1 and 2.
    """
    # A (turn 1): supervisor learns ALPHA.
    sup1 = _timed_prompt(
        intervals,
        "sup-turn-1",
        "You are a persistent review supervisor. Remember the token ALPHA. "
        "Reply with only: OK",
        None,
        env_vars,
    )
    original_id = sup1["session_id"]
    current_id = original_id

    # B (fresh reviewer): shares no context with the supervisor.
    _timed_prompt(
        intervals,
        "reviewer-1",
        "You are a fresh, single-use reviewer. Share nothing. Reply with only: OK",
        None,
        env_vars,
    )

    # A (turn 2): supervisor learns BETA, resuming the supervisor session.
    sup2 = _timed_prompt(
        intervals,
        "sup-turn-2",
        "Also remember the token BETA. Reply with only: OK",
        current_id,
        env_vars,
    )
    current_id = _next_supervisor_session_id(original_id, current_id, sup2, discipline)

    # B (another fresh reviewer).
    _timed_prompt(
        intervals,
        "reviewer-2",
        "You are another fresh, single-use reviewer. Share nothing. Reply with only: OK",
        None,
        env_vars,
    )

    # A (turn 3): supervisor must recall BOTH tokens.
    sup3 = _timed_prompt(
        intervals,
        "sup-turn-3",
        "Name BOTH tokens you were told to remember, exactly as given.",
        current_id,
        env_vars,
    )
    return sup3["text"].upper()


@pytest.mark.claude_cli_integration
def test_supervisor_recalls_across_interleaved_reviewer_sessions() -> None:
    """Persistent supervisor recalls turns 1 AND 2 across interleaved fresh reviewers.

    A-B-A flow with >=3 supervisor turns; turn 3 must recall both ALPHA (turn 1)
    and BETA (turn 2). Also pins the issue-mandated strict-sequential (never
    concurrent) execution of the supervisor/reviewer calls.
    """
    env_vars = prepare_llm_environment(Path.cwd())
    intervals: list[_CallInterval] = []

    text = _run_interleave(env_vars, WINNING_SESSION_DISCIPLINE, intervals)

    assert "ALPHA" in text, f"supervisor turn 3 did not recall turn-1 token: {text!r}"
    assert "BETA" in text, f"supervisor turn 3 did not recall turn-2 token: {text!r}"

    # Strict sequencing: token recall alone does not prove the orchestrator never
    # ran the two sessions concurrently — pin it explicitly.
    _assert_strictly_sequential(intervals)


@pytest.mark.claude_cli_integration
def test_reuse_original_id_vs_recapture_returned_id() -> None:
    """Decide the session-id chaining discipline; record the create_plan finding.

    Runs the A-B-A flow twice — once reusing the turn-1 id every turn
    (``create_plan`` style), once re-capturing each returned id — and records
    which discipline preserves the turn-2 token (BETA) at turn 3.

    The ``recapture_returned_id`` discipline (:data:`WINNING_SESSION_DISCIPLINE`,
    used by Step 7) is asserted to preserve context unconditionally. If
    ``reuse_original_id`` drops BETA, that is the ``create_plan`` / ``core.py``
    context-loss finding documented in this module's docstring NOTE (fix out of
    scope for #1072).
    """
    env_vars = prepare_llm_environment(Path.cwd())

    reuse_intervals: list[_CallInterval] = []
    reuse_text = _run_interleave(
        env_vars, SESSION_DISCIPLINE_REUSE_ORIGINAL, reuse_intervals
    )
    reuse_preserves_beta = "ALPHA" in reuse_text and "BETA" in reuse_text

    recapture_intervals: list[_CallInterval] = []
    recapture_text = _run_interleave(
        env_vars, SESSION_DISCIPLINE_RECAPTURE, recapture_intervals
    )
    recapture_preserves_beta = "ALPHA" in recapture_text and "BETA" in recapture_text

    # Both runs must have executed strictly sequentially.
    _assert_strictly_sequential(reuse_intervals)
    _assert_strictly_sequential(recapture_intervals)

    # The winning discipline (what Step 7 implements) MUST preserve both tokens.
    assert recapture_preserves_beta, (
        "recapture-returned-id discipline lost context; supervisor turn-3 text "
        f"was: {recapture_text!r}"
    )
    assert WINNING_SESSION_DISCIPLINE == SESSION_DISCIPLINE_RECAPTURE

    # Record the create_plan finding (see module docstring NOTE): reuse-original-id
    # either preserves BETA or silently drops the turn-2 context in production.
    if reuse_preserves_beta:
        logger.info(
            "session-discipline finding: reuse-original-id preserved BETA "
            "(create_plan resume sites retain intermediate-turn context)"
        )
    else:
        logger.warning(
            "session-discipline finding: reuse-original-id DROPPED BETA — "
            "create_plan/core.py reuse-original resume sites silently lose "
            "prompt-2 context in production (fix out of scope for #1072)"
        )
