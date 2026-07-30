"""Step 7 — review engine core loop tests (mocked LLM).

These deterministic tests drive :func:`run_review_workflow` with a mocked
``prompt_llm`` and mocked git / label / failure helpers. They exercise the
shared loop against ``REVIEW_PLAN`` (``run_after_steps=False``), so the
``_after_steps`` stub always returns ``None`` here — Step 8 covers the
after-steps behaviour separately.

Call order per round:
    1. fresh reviewer (``session_id=None``)               -> prompt_llm call
    2. supervisor verdict (persistent session)            -> prompt_llm call
    3. (only on a ``tasks`` verdict) reviewer resume       -> prompt_llm call

so the ``prompt_llm`` ``side_effect`` list is built to match that sequence.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflows.review import core, reviewer
from mcp_coder.workflows.review.config import REVIEW_PLAN

# --- verdict payloads -------------------------------------------------------

_DISMISS = '```json\n{"decision": "dismiss"}\n```'
_TASKS = '```json\n{"decision": "tasks", "tasks": ["Fix the bug at foo.py:1"]}\n```'
_ESCALATE = '```json\n{"decision": "escalate", "escalate_reason": "needs a human"}\n```'
_GARBAGE = "no verdict here, just prose"

_REPORT = "foo.py:1 — high — something is wrong"


def _resp(text: str, session_id: str = "sup-1") -> dict[str, Any]:
    """Build a minimal LLMResponseDict-shaped mock response."""
    return {
        "text": text,
        "session_id": session_id,
        "version": "1.0",
        "timestamp": "2026-01-01T00:00:00",
        "provider": "claude",
        "raw_response": {},
    }


def _reviewer(text: str = _REPORT, session_id: str = "rev-1") -> dict[str, Any]:
    """Reviewer response (distinct session id from the supervisor)."""
    return _resp(text, session_id=session_id)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every external the core loop touches; expose the mocks."""
    mocks = SimpleNamespace()

    mocks.prompt_llm = MagicMock(name="prompt_llm")
    monkeypatch.setattr(reviewer, "prompt_llm", mocks.prompt_llm)

    monkeypatch.setattr(reviewer, "prepare_llm_environment", MagicMock(return_value={}))

    mocks.run_formatters = MagicMock(return_value=True)
    monkeypatch.setattr(core, "run_formatters", mocks.run_formatters)
    mocks.commit_changes = MagicMock(return_value=True)
    monkeypatch.setattr(core, "commit_changes", mocks.commit_changes)
    mocks.push_changes = MagicMock(return_value=True)
    monkeypatch.setattr(core, "push_changes", mocks.push_changes)

    # By default every round registers a change (dirty working dir).
    mocks.get_latest_commit_sha = MagicMock(return_value="SHA0")
    monkeypatch.setattr(core, "get_latest_commit_sha", mocks.get_latest_commit_sha)
    mocks.is_working_directory_clean = MagicMock(return_value=False)
    monkeypatch.setattr(
        core, "is_working_directory_clean", mocks.is_working_directory_clean
    )

    monkeypatch.setattr(
        core, "get_current_branch_name", MagicMock(return_value="1072-review")
    )
    monkeypatch.setattr(core, "IssueManager", MagicMock(name="IssueManager"))

    mocks.update_workflow_label = MagicMock(return_value=True)
    monkeypatch.setattr(core, "update_workflow_label", mocks.update_workflow_label)
    mocks.handle_workflow_failure = MagicMock()
    monkeypatch.setattr(core, "handle_workflow_failure", mocks.handle_workflow_failure)

    # Present so the plan lane can assert it is never called (thread_pr_feedback
    # is False for REVIEW_PLAN); a stray call would surface as a real GitHub hit.
    mocks.collect_branch_status = MagicMock(
        return_value=SimpleNamespace(pr_feedback_text=None)
    )
    monkeypatch.setattr(core, "collect_branch_status", mocks.collect_branch_status)

    return mocks


def _run(project_dir: Path, **kwargs: Any) -> int:
    """Invoke the workflow with label updates on unless overridden."""
    params: dict[str, Any] = {
        "config": REVIEW_PLAN,
        "project_dir": project_dir,
        "provider": "claude",
        "update_issue_labels": True,
        "post_issue_comments": True,
    }
    params.update(kwargs)
    return core.run_review_workflow(**params)


def _label_transition(mock: MagicMock) -> tuple[str, str]:
    """Return the (from_label_id, to_label_id) of the last label update."""
    kwargs = mock.call_args.kwargs
    return kwargs["from_label_id"], kwargs["to_label_id"]


def test_dismiss_round_one_succeeds(env: SimpleNamespace, tmp_path: Path) -> None:
    """A round-1 dismiss returns 0, sets the success label, posts no failure."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    env.handle_workflow_failure.assert_not_called()
    env.update_workflow_label.assert_called_once()
    from_id, to_id = _label_transition(env.update_workflow_label)
    assert from_id == REVIEW_PLAN.busy_label_id
    assert to_id == REVIEW_PLAN.success_label_id


def test_escalate_sets_escalate_label_and_logs_reason(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """An escalate verdict returns 0, escalate label, log reason, no failure."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_ESCALATE)]

    result = _run(tmp_path)

    assert result == 0
    env.handle_workflow_failure.assert_not_called()
    from_id, to_id = _label_transition(env.update_workflow_label)
    assert from_id == REVIEW_PLAN.busy_label_id
    assert to_id == REVIEW_PLAN.escalate_label_id

    log = (tmp_path / "pr_info" / "plan_review_log_1.md").read_text(encoding="utf-8")
    assert "needs a human" in log


def test_tasks_then_dismiss_resumes_reviewer(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A tasks verdict resumes the reviewer session, then converges to success."""
    env.prompt_llm.side_effect = [
        _reviewer(),  # round 1 fresh reviewer
        _resp(_TASKS),  # round 1 supervisor -> tasks
        _reviewer(text="fixed", session_id="rev-1"),  # round 1 apply-tasks resume
        _reviewer(),  # round 2 fresh reviewer
        _resp(_DISMISS),  # round 2 supervisor -> dismiss
    ]

    result = _run(
        tmp_path,
        mcp_config="cfg.json",
        settings_file="s.json",
        execution_dir=tmp_path,
    )

    assert result == 0
    assert env.prompt_llm.call_count == 5
    # The apply-tasks call resumes the reviewer session and carries the task.
    apply_call = env.prompt_llm.call_args_list[2]
    assert apply_call.kwargs["session_id"] == "rev-1"
    assert "Fix the bug at foo.py:1" in apply_call.args[0]
    # The post-apply commit runs with the same session params as the reviewer.
    env.commit_changes.assert_called_once_with(
        tmp_path,
        "claude",
        mcp_config="cfg.json",
        execution_dir=str(tmp_path),
        settings_file="s.json",
    )
    env.push_changes.assert_called_once()
    _, to_id = _label_transition(env.update_workflow_label)
    assert to_id == REVIEW_PLAN.success_label_id


def test_reviewer_is_fresh_each_round(env: SimpleNamespace, tmp_path: Path) -> None:
    """Each round's opening reviewer call uses a fresh (None) session id."""
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),
        _reviewer(),
        _resp(_DISMISS),
    ]

    _run(tmp_path)

    # Calls 0 (round 1) and 3 (round 2) are the fresh reviewers.
    assert env.prompt_llm.call_args_list[0].kwargs["session_id"] is None
    assert env.prompt_llm.call_args_list[3].kwargs["session_id"] is None


def test_supervisor_session_recaptured(env: SimpleNamespace, tmp_path: Path) -> None:
    """The supervisor is resumed with the id returned by its previous turn."""
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS, session_id="sup-A"),  # round 1 supervisor returns sup-A
        _reviewer(session_id="rev-1"),
        _reviewer(),
        _resp(_DISMISS, session_id="sup-B"),  # round 2 supervisor
    ]

    _run(tmp_path)

    # Round 2 supervisor (call index 4) resumes with the id from round 1 (sup-A).
    assert env.prompt_llm.call_args_list[4].kwargs["session_id"] == "sup-A"


def test_unparseable_verdict_fails_after_repairs(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Verdict garbage after 2 repair retries returns 1 with the general label."""
    env.prompt_llm.side_effect = [
        _reviewer(),  # reviewer
        _resp(_GARBAGE),  # supervisor (bad)
        _resp(_GARBAGE),  # repair 1 (bad)
        _resp(_GARBAGE),  # repair 2 (bad)
    ]

    result = _run(tmp_path)

    assert result == 1
    assert env.prompt_llm.call_count == 4  # reviewer + supervisor + 2 repairs
    env.handle_workflow_failure.assert_called_once()
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_PLAN.failure_labels["general"]


def test_repair_recovers_valid_verdict(env: SimpleNamespace, tmp_path: Path) -> None:
    """A repaired verdict (valid on retry 1) is honored — dismiss succeeds."""
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_GARBAGE),  # supervisor bad
        _resp(_DISMISS),  # repair 1 good
    ]

    result = _run(tmp_path)

    assert result == 0
    env.handle_workflow_failure.assert_not_called()


def test_rounds_cap_exhausted_fails(env: SimpleNamespace, tmp_path: Path) -> None:
    """tasks every round hits the cap and fails with the rounds label."""
    per_round = [_reviewer(), _resp(_TASKS), _reviewer(session_id="rev-1")]
    env.prompt_llm.side_effect = per_round * core.REVIEW_MAX_ROUNDS

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_PLAN.failure_labels["rounds"]


def test_silent_no_op_is_logged_and_loops(env: SimpleNamespace, tmp_path: Path) -> None:
    """tasks with no change (same sha + clean dir) logs a no-op yet keeps looping."""
    env.is_working_directory_clean.return_value = True  # clean == no change applied
    per_round = [_reviewer(), _resp(_TASKS), _reviewer(session_id="rev-1")]
    env.prompt_llm.side_effect = per_round * core.REVIEW_MAX_ROUNDS

    result = _run(tmp_path)

    assert result == 1  # cap still reached
    log = (tmp_path / "pr_info" / "plan_review_log_1.md").read_text(encoding="utf-8")
    assert "no-op" in log


def test_timeout_maps_to_timeout_label(env: SimpleNamespace, tmp_path: Path) -> None:
    """An LLMTimeoutError from the reviewer maps to the timeout failure label."""
    env.prompt_llm.side_effect = LLMTimeoutError("slow")

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_PLAN.failure_labels["timeout"]


def test_mcp_unavailable_maps_to_mcp_label(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A McpServersUnavailableError maps to the mcp failure label."""
    env.prompt_llm.side_effect = McpServersUnavailableError("down", {})

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_PLAN.failure_labels["mcp_unavailable"]


def test_commit_failure_fails_run_and_skips_push(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """commit_changes False -> return 1, general label, log entry, no push."""
    env.commit_changes.return_value = False
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),
    ]

    result = _run(tmp_path)

    assert result == 1
    env.push_changes.assert_not_called()
    env.handle_workflow_failure.assert_called_once()
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_PLAN.failure_labels["general"]
    assert "commit-failed" in failure.message

    log = (tmp_path / "pr_info" / "plan_review_log_1.md").read_text(encoding="utf-8")
    assert "commit-failed" in log


def test_push_failure_fails_run(env: SimpleNamespace, tmp_path: Path) -> None:
    """push_changes False -> return 1, general label, log entry."""
    env.push_changes.return_value = False
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),
    ]

    result = _run(tmp_path)

    assert result == 1
    env.commit_changes.assert_called_once()
    env.handle_workflow_failure.assert_called_once()
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_PLAN.failure_labels["general"]
    assert "push-failed" in failure.message

    log = (tmp_path / "pr_info" / "plan_review_log_1.md").read_text(encoding="utf-8")
    assert "push-failed" in log


def test_clean_tree_round_proceeds_normally(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A round with no file changes (commit no-ops True) keeps looping to success."""
    env.is_working_directory_clean.return_value = True
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),
        _reviewer(),
        _resp(_DISMISS),
    ]

    result = _run(tmp_path)

    assert result == 0
    env.handle_workflow_failure.assert_not_called()


def test_labels_not_touched_when_gating_off(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """With update_issue_labels False, no real label transition is attempted."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path, update_issue_labels=False)

    assert result == 0
    env.update_workflow_label.assert_not_called()


# --- Step 5: broadened excepts + empty-report retry + enriched comment ------


def test_generic_exception_at_reviewer_fails_general(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A generic (non-LLM) exception at the fresh reviewer is categorized general.

    The broadened ``except`` must catch it and route through ``_fail`` with the
    general label + a comment + exit 1 — never an uncaught escape.
    """
    env.prompt_llm.side_effect = RuntimeError("kaboom")

    result = _run(tmp_path)

    assert result == 1
    env.handle_workflow_failure.assert_called_once()
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_PLAN.failure_labels["general"]
    # A generic exception is not retried — it fails on the first invocation.
    assert env.prompt_llm.call_count == 1


def test_empty_reports_retry_inline_then_fail_general(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Whitespace-only reports are retried inline (no round consumed) then fail."""
    env.prompt_llm.side_effect = [
        _reviewer(text="   "),
        _reviewer(text="\n\t "),
        _reviewer(text="  "),
    ]

    result = _run(tmp_path)

    assert result == 1
    # The reviewer is re-invoked as an INNER retry, all within round 1.
    assert env.prompt_llm.call_count == core.EMPTY_REPORT_RETRIES
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_PLAN.failure_labels["general"]
    # No round was consumed by the inner retry: the comment still reports round 1.
    comment = env.handle_workflow_failure.call_args.args[1]
    assert "Round: 1" in comment


def test_empty_then_valid_report_recovers(env: SimpleNamespace, tmp_path: Path) -> None:
    """A whitespace report retried once then valid proceeds to a normal verdict."""
    env.prompt_llm.side_effect = [
        _reviewer(text="   "),  # empty -> inner retry
        _reviewer(),  # valid report
        _resp(_DISMISS),  # supervisor -> dismiss
    ]

    result = _run(tmp_path)

    assert result == 0
    env.handle_workflow_failure.assert_not_called()


def test_body_escape_is_netted_by_guard(
    env: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``SystemExit`` escaping ``body()`` is netted (general) then re-raised.

    ``SystemExit`` (SIGTERM / ``sys.exit``) is not an ``Exception``, so it slips
    past the in-body classify-and-fail paths and is caught only by the guard,
    which maps it to the general label and re-raises.
    """
    net = MagicMock()
    monkeypatch.setattr(
        "mcp_coder.workflow_utils.failure_handling.handle_workflow_failure", net
    )
    env.prompt_llm.side_effect = SystemExit(1)

    with pytest.raises(SystemExit):
        _run(tmp_path)

    net.assert_called_once()
    failure = net.call_args.args[0]
    assert failure.category == REVIEW_PLAN.failure_labels["general"]
    comment = net.call_args.args[1]
    assert "review terminated unexpectedly" in comment


def test_deliberate_fail_comment_carries_round_verdict_elapsed(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A deliberate failure comment is enriched with round, verdict, elapsed."""
    env.commit_changes.return_value = False  # deliberate _fail after a tasks verdict
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),
    ]

    result = _run(tmp_path)

    assert result == 1
    comment = env.handle_workflow_failure.call_args.args[1]
    assert "Round: 1" in comment
    assert "Verdict: tasks" in comment
    assert "Elapsed:" in comment


# --- Step 3: PR-feedback threading (plan lane skips it) ---------------------


class TestPrFeedbackNote:
    """The pure framing helper."""

    def test_none_in_none_out(self) -> None:
        assert core._pr_feedback_note(None) is None

    def test_empty_in_none_out(self) -> None:
        assert core._pr_feedback_note("") is None

    def test_wraps_non_empty_text(self) -> None:
        note = core._pr_feedback_note("changes requested on foo.py")
        assert note is not None
        assert "open PR review feedback" in note  # framing preamble
        assert "changes requested on foo.py" in note  # raw text preserved


def test_plan_lane_skips_pr_feedback(env: SimpleNamespace, tmp_path: Path) -> None:
    """REVIEW_PLAN makes no branch-status call and threads no PR feedback."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    env.collect_branch_status.assert_not_called()
    # Fresh reviewer prompt carries no PR-feedback note...
    assert "open PR review feedback" not in env.prompt_llm.call_args_list[0].args[0]
    # ...and the supervisor got the bare reviewer report.
    assert "## Open PR review feedback" not in env.prompt_llm.call_args_list[1].args[0]
