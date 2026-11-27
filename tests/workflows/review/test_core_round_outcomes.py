"""Review-loop tests for what a round records and passes on.

These drive :func:`run_review_workflow` with the shared ``env`` fixture from
``conftest`` (all LLM and git externals mocked). Call order per round:
fresh reviewer, supervisor verdict, then (on ``tasks``) the reviewer resume.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from mcp_coder.workflows.review.config import REVIEW_PLAN
from tests.workflows.review.conftest import (
    _DISMISS,
    _REPORT_MEDIUM,
    _TASKS,
    _resp,
    _reviewer,
    _run,
    _status,
)


def _final_resp(text: str, result: str, session_id: str = "rev-1") -> dict[str, Any]:
    """Reviewer response whose ``raw_response`` events end in a ``done`` event."""
    response = _resp(text, session_id=session_id)
    response["raw_response"] = {
        "events": [
            {"type": "text_delta", "text": text},
            {"type": "done", "result": result},
        ]
    }
    return response


def _log(tmp_path: Path) -> str:
    """Read the round log of the implementation lane's first run."""
    return (tmp_path / "pr_info" / "implementation_review_log_1.md").read_text(
        encoding="utf-8"
    )


def test_round_uses_the_final_reviewer_message(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Narration before the final message reaches neither the log nor the supervisor."""
    env.prompt_llm.side_effect = [
        _final_resp("Still reviewing.a.py:1 — high — x", "a.py:1 — high — x"),
        _resp(_DISMISS),
    ]

    result = _run(tmp_path)

    assert result == 0
    log = _log(tmp_path)
    assert "a.py:1 — high — x" in log
    assert "Still reviewing" not in log
    supervisor_prompt = env.prompt_llm.call_args_list[1].args[0]
    assert "Still reviewing" not in supervisor_prompt


def test_empty_final_message_falls_back_without_retry(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """An empty final result uses the joined text; the empty-report retry stays off."""
    env.prompt_llm.side_effect = [
        _final_resp("a.py:1 — high — x", ""),
        _resp(_DISMISS),
    ]

    result = _run(tmp_path)

    assert result == 0
    assert env.prompt_llm.call_count == 2


def test_supervisor_is_told_no_pr_exists(env: SimpleNamespace, tmp_path: Path) -> None:
    """Implementation lane without a PR: the supervisor input says so."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    supervisor_prompt = env.prompt_llm.call_args_list[1].args[0]
    assert "no PR exists yet" in supervisor_prompt


def test_supervisor_is_told_the_pr_number(env: SimpleNamespace, tmp_path: Path) -> None:
    """Implementation lane with a PR: the supervisor input names it."""
    env.collect_branch_status.return_value = _status(pr_found=True, pr_number=7)
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    supervisor_prompt = env.prompt_llm.call_args_list[1].args[0]
    assert "PR #7" in supervisor_prompt


def test_plan_lane_supervisor_has_no_review_state(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """The plan lane fetches no branch status, so no PR-state section."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path, config=REVIEW_PLAN)

    assert result == 0
    supervisor_prompt = env.prompt_llm.call_args_list[1].args[0]
    assert "## Review state" not in supervisor_prompt


_APPLY_REPLY = "not applied: no PR exists\nfoo.py:1 — high — x"


def test_noop_round_logs_the_task_outcomes(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """The apply reply's outcome lines follow the no-op token in **Changes**."""
    env.round_applied.return_value = False
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(_APPLY_REPLY),
        _reviewer(),
        _resp(_DISMISS),
    ]

    result = _run(tmp_path)

    assert result == 0
    assert "**Changes**:\n\nno-op\nnot applied: no PR exists\n" in _log(tmp_path)


def test_commit_failed_round_ignores_the_task_outcomes(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A failed commit records only ``commit-failed`` in **Changes**."""
    env.commit_changes.return_value = False
    env.prompt_llm.side_effect = [_reviewer(), _resp(_TASKS), _reviewer(_APPLY_REPLY)]

    result = _run(tmp_path)

    assert result == 1
    log = _log(tmp_path)
    assert "**Changes**:\n\ncommit-failed\n\n**Escalate reason**" in log
    assert "not applied" not in log


def test_push_failed_round_ignores_the_task_outcomes(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A failed push records only ``push-failed`` in **Changes**."""
    env.push_changes.return_value = False
    env.prompt_llm.side_effect = [_reviewer(), _resp(_TASKS), _reviewer(_APPLY_REPLY)]

    result = _run(tmp_path)

    assert result == 1
    log = _log(tmp_path)
    assert "**Changes**:\n\npush-failed\n\n**Escalate reason**" in log
    assert "not applied" not in log


def test_noop_round_is_reported_to_the_next_supervisor(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Round 2's supervisor input names round 1's unapplied tasks and outcomes."""
    env.round_applied.side_effect = [False, True]
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(_APPLY_REPLY),
        _reviewer(),
        _resp(_DISMISS),
    ]

    result = _run(tmp_path)

    assert result == 0
    supervisor_prompt = env.prompt_llm.call_args_list[4].args[0]
    review_state = supervisor_prompt.split("## Review state", 1)[1]
    assert "Fix the bug at foo.py:1" in review_state
    assert "NOT applied" in review_state
    assert "not applied: no PR exists" in review_state


def test_applied_round_sends_no_noop_note(env: SimpleNamespace, tmp_path: Path) -> None:
    """After a round that changed files, the next supervisor gets no no-op note."""
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(_APPLY_REPLY),
        _reviewer(),
        _resp(_DISMISS),
    ]

    result = _run(tmp_path)

    assert result == 0
    assert "NOT applied" not in env.prompt_llm.call_args_list[4].args[0]


def test_pending_noop_note_exempts_round_from_severity_floor(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A round after a no-op round is never severity-downgraded.

    Rounds 1-2 change nothing, so round 3 (the strict round) with an
    all-``medium`` report still runs its apply-tasks resume.
    """
    env.round_applied.side_effect = [False, False, True]
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),  # round 1: no-op
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),  # round 2: no-op
        _reviewer(_REPORT_MEDIUM),
        _resp(_TASKS),  # round 3: medium + no-op note -> exempt from the floor
        _reviewer(session_id="rev-1"),  # round 3 apply-tasks
        _reviewer(),
        _resp(_DISMISS),  # round 4 -> success
    ]

    result = _run(tmp_path)

    assert result == 0
    assert env.prompt_llm.call_count == 11
    apply_call = env.prompt_llm.call_args_list[8]
    assert apply_call.kwargs["session_id"] == "rev-1"
    assert "Fix the bug at foo.py:1" in apply_call.args[0]
