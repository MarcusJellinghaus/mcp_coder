"""Step 8 — after-steps tests (base-branch injection + rebase + CI-as-finding).

These deterministic tests drive :func:`run_review_workflow` against
``REVIEW_IMPLEMENTATION`` (``run_after_steps=True``), so the ``_after_steps``
hook exercises the real rebase gate and CI gate. The LLM (``prompt_llm``), the
rebase step (``_attempt_rebase_and_push``), the CI step (``check_and_fix_ci``)
and base-branch detection (``detect_base_branch``) are all mocked.

Call order per round mirrors Step 7:
    1. fresh reviewer (``session_id=None``)               -> prompt_llm call
    2. supervisor verdict (persistent session)            -> prompt_llm call
    3. (only on a ``tasks`` verdict) reviewer resume       -> prompt_llm call

``_after_steps`` then runs the rebase + CI gates after a dismiss (final gate)
or after a ``tasks`` application (mid-loop).
"""

import inspect
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.checks.branch_status import CIStatus
from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflows.review import core, handoff, reviewer, steps
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION, REVIEW_PLAN

# --- verdict payloads -------------------------------------------------------

_DISMISS = '```json\n{"decision": "dismiss"}\n```'
_TASKS = '```json\n{"decision": "tasks", "tasks": ["Fix the bug at foo.py:1"]}\n```'

_REPORT = "foo.py:1 — high — something is wrong"
_REPORT_MEDIUM = "foo.py:1 — medium — a moderate concern"


def _status(
    text: str | None = None,
    undeterminable: bool = False,
    ci_status: CIStatus = CIStatus.PASSED,
) -> SimpleNamespace:
    """Build a branch-status stand-in with the fields the review loop reads."""
    return SimpleNamespace(
        pr_feedback_text=text,
        pr_feedback_undeterminable=undeterminable,
        ci_status=ci_status,
    )


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
    """Patch every external the core loop + after-steps touch; expose the mocks."""
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
        steps, "get_current_branch_name", MagicMock(return_value="1072-review")
    )
    mocks.issue_manager = MagicMock(name="IssueManager")
    monkeypatch.setattr(handoff, "IssueManager", mocks.issue_manager)

    # Terminal-path log flush (handoff._flush_round_log commit + push): mocked so
    # the flush never touches real git; tests assert the commit fired.
    mocks.commit_all_changes = MagicMock(
        return_value={"success": True, "commit_hash": "FLUSHSHA"}
    )
    monkeypatch.setattr(handoff, "commit_all_changes", mocks.commit_all_changes)
    mocks.flush_push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "push_changes", mocks.flush_push)

    mocks.update_workflow_label = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "update_workflow_label", mocks.update_workflow_label)
    mocks.handle_workflow_failure = MagicMock()
    monkeypatch.setattr(
        handoff, "handle_workflow_failure", mocks.handle_workflow_failure
    )

    # After-steps externals: default to a clean rebase + green CI + a base branch.
    mocks.detect_base_branch = MagicMock(return_value="main")
    monkeypatch.setattr(steps, "detect_base_branch", mocks.detect_base_branch)
    mocks.attempt_rebase_and_push = MagicMock(return_value=True)
    monkeypatch.setattr(
        steps, "_attempt_rebase_and_push", mocks.attempt_rebase_and_push
    )
    mocks.check_and_fix_ci = MagicMock(return_value=True)
    monkeypatch.setattr(steps, "check_and_fix_ci", mocks.check_and_fix_ci)

    # PR-feedback fetch (implementation lane): default to a report with no open
    # feedback so existing tests see no note; individual tests override the
    # return value to exercise the threading.
    mocks.collect_branch_status = MagicMock(return_value=_status())
    monkeypatch.setattr(core, "collect_branch_status", mocks.collect_branch_status)

    return mocks


def _run(project_dir: Path, **kwargs: Any) -> int:
    """Invoke the workflow (implementation lane) with label updates on."""
    params: dict[str, Any] = {
        "config": REVIEW_IMPLEMENTATION,
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


# --- base-branch injection --------------------------------------------------


def test_impl_injects_base_branch_into_reviewer_prompt(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """REVIEW_IMPLEMENTATION detects and injects a base branch into the prompt."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    env.detect_base_branch.assert_called_once_with(tmp_path)
    # The fresh reviewer prompt has its {base_branch} placeholder substituted.
    reviewer_prompt = env.prompt_llm.call_args_list[0].args[0]
    assert "main" in reviewer_prompt
    assert "{base_branch}" not in reviewer_prompt


def test_plan_does_not_detect_base_branch(env: SimpleNamespace, tmp_path: Path) -> None:
    """REVIEW_PLAN leaves the base branch None and never calls detection."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path, config=REVIEW_PLAN)

    assert result == 0
    env.detect_base_branch.assert_not_called()


# --- dismiss final gate: rebase + CI ---------------------------------------


def test_dismiss_rebase_clean_ci_green_succeeds(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """dismiss + clean rebase + green CI -> success (ready_pr), no failure."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    env.attempt_rebase_and_push.assert_called_once_with(tmp_path)
    env.check_and_fix_ci.assert_called_once()
    # CI reuses implement's headers, overriding only the session dir name.
    assert (
        env.check_and_fix_ci.call_args.kwargs["session_dir_name"]
        == REVIEW_IMPLEMENTATION.session_dir_name
    )
    env.handle_workflow_failure.assert_not_called()
    from_id, to_id = _label_transition(env.update_workflow_label)
    assert from_id == REVIEW_IMPLEMENTATION.busy_label_id
    assert to_id == REVIEW_IMPLEMENTATION.success_label_id


def test_dismiss_rebase_conflict_routes_to_needs_human(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """dismiss + unresolved rebase -> needs-human (07:code-review), never success."""
    env.attempt_rebase_and_push.return_value = False
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0  # needs-human handoff, not an error
    # Rebase gate short-circuits: CI is never reached, no failure is raised.
    env.check_and_fix_ci.assert_not_called()
    env.handle_workflow_failure.assert_not_called()
    from_id, to_id = _label_transition(env.update_workflow_label)
    assert from_id == REVIEW_IMPLEMENTATION.busy_label_id
    assert to_id == REVIEW_IMPLEMENTATION.escalate_label_id  # never success
    assert to_id != REVIEW_IMPLEMENTATION.success_label_id

    log = (tmp_path / "pr_info" / "implementation_review_log_1.md").read_text(
        encoding="utf-8"
    )
    assert "rebase" in log


def test_rebase_slot_references_issue_1066(env: SimpleNamespace) -> None:
    """The needs-human rebase slot carries the #1066 NotYetImplemented marker."""
    source = inspect.getsource(steps._after_steps)
    assert "#1066" in source
    assert "NotYetImplemented" in source


def test_dismiss_ci_red_fails_with_ci_label(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """dismiss + red CI on the final gate -> 1 with the code_review_ci label."""
    env.check_and_fix_ci.return_value = False
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 1
    env.handle_workflow_failure.assert_called_once()
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["ci"]


def test_dismiss_ci_timeout_maps_to_timeout_label(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A CI-phase LLMTimeoutError maps to the timeout failure label."""
    env.check_and_fix_ci.side_effect = LLMTimeoutError("slow")
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["timeout"]


def test_dismiss_ci_mcp_down_maps_to_mcp_label(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A CI-phase McpServersUnavailableError maps to the mcp failure label."""
    env.check_and_fix_ci.side_effect = McpServersUnavailableError("down", {})
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["mcp_unavailable"]


# --- CI-as-finding (mid-loop) ----------------------------------------------


def test_tasks_ci_red_carries_note_into_next_reviewer(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A mid-loop red CI does not fail: the note reaches the next reviewer."""
    # Round 1 tasks -> CI red (mid-loop finding); round 2 dismiss -> CI green.
    env.check_and_fix_ci.side_effect = [False, True]
    env.prompt_llm.side_effect = [
        _reviewer(),  # round 1 fresh reviewer
        _resp(_TASKS),  # round 1 supervisor -> tasks
        _reviewer(session_id="rev-1"),  # round 1 apply-tasks resume
        _reviewer(),  # round 2 fresh reviewer (should carry the CI note)
        _resp(_DISMISS),  # round 2 supervisor -> dismiss
    ]

    result = _run(tmp_path)

    assert result == 0
    env.handle_workflow_failure.assert_not_called()
    # Round 2's fresh reviewer (call index 3) carries the CI finding note.
    round2_reviewer_prompt = env.prompt_llm.call_args_list[3].args[0]
    assert "open CI finding" in round2_reviewer_prompt
    # Round 1's fresh reviewer (call index 0) did not (nothing pending yet).
    assert "open CI finding" not in env.prompt_llm.call_args_list[0].args[0]
    _, to_id = _label_transition(env.update_workflow_label)
    assert to_id == REVIEW_IMPLEMENTATION.success_label_id


def test_tasks_ci_green_no_note_and_normal_loop(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A mid-loop green CI carries no note into the next reviewer prompt."""
    env.check_and_fix_ci.side_effect = [True, True]
    env.prompt_llm.side_effect = [
        _reviewer(),  # round 1 fresh reviewer
        _resp(_TASKS),  # round 1 supervisor -> tasks
        _reviewer(session_id="rev-1"),  # round 1 apply-tasks resume
        _reviewer(),  # round 2 fresh reviewer (no note expected)
        _resp(_DISMISS),  # round 2 supervisor -> dismiss
    ]

    result = _run(tmp_path)

    assert result == 0
    assert "open CI finding" not in env.prompt_llm.call_args_list[3].args[0]


def test_tasks_ci_red_every_round_caps_with_ci_label(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Red CI on every tasks round hits the cap with the ci label, not rounds.

    CI stays terminal at the cap (RC=1), but the last round's log is still
    flushed to the committed review log before failing.
    """
    env.check_and_fix_ci.return_value = False
    per_round = [_reviewer(), _resp(_TASKS), _reviewer(session_id="rev-1")]
    env.prompt_llm.side_effect = per_round * core.REVIEW_MAX_ROUNDS

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    # Open CI finding at the cap wins over the plain rounds reason (17f-ci).
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["ci"]
    # The last round's log is flushed to the committed review log before _fail.
    env.commit_all_changes.assert_called()


def test_tasks_rebase_conflict_routes_to_needs_human(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A mid-loop unresolved rebase also routes to needs-human, never success."""
    env.attempt_rebase_and_push.return_value = False
    env.prompt_llm.side_effect = [
        _reviewer(),  # round 1 fresh reviewer
        _resp(_TASKS),  # round 1 supervisor -> tasks
        _reviewer(session_id="rev-1"),  # round 1 apply-tasks resume
    ]

    result = _run(tmp_path)

    assert result == 0  # needs-human handoff
    env.handle_workflow_failure.assert_not_called()
    _, to_id = _label_transition(env.update_workflow_label)
    assert to_id == REVIEW_IMPLEMENTATION.escalate_label_id


# --- Step 5: broadened CI-gate except (scoped, control-flow preserved) ------


def test_dismiss_ci_generic_exception_fails_general(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A generic exception escaping ``check_and_fix_ci`` is categorized general.

    The broadened ``except`` scoped to the CI call must catch it (not an uncaught
    escape) and route it to the general failure label.
    """
    env.check_and_fix_ci.side_effect = RuntimeError("ci boom")
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 1
    env.handle_workflow_failure.assert_called_once()
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["general"]


def test_broadened_ci_except_does_not_swallow_rebase(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """The rebase gate sits outside the broadened CI except: it still escalates.

    An unresolved rebase must route to needs-human (escalate, return 0) — the
    broadened ``except`` around ``check_and_fix_ci`` must not swallow it, and CI
    is never even reached.
    """
    env.attempt_rebase_and_push.return_value = False
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0  # needs-human handoff, never a failure label
    env.check_and_fix_ci.assert_not_called()
    env.handle_workflow_failure.assert_not_called()
    _, to_id = _label_transition(env.update_workflow_label)
    assert to_id == REVIEW_IMPLEMENTATION.escalate_label_id


def test_broadened_ci_except_does_not_swallow_ci_carry_forward(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A returned (non-raised) red CI still routes as the ``ci`` finding reason.

    ``check_and_fix_ci`` returning ``False`` must map to the ``ci`` reason/label,
    not be collapsed into the general bucket by the broadened ``except``.
    """
    env.check_and_fix_ci.return_value = False
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["ci"]
    assert failure.category != REVIEW_IMPLEMENTATION.failure_labels["general"]


# --- Step 3: PR-feedback threading (implementation lane) --------------------


def test_impl_lane_threads_pr_feedback_into_both_targets(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Open feedback reaches the fresh reviewer prompt AND the supervisor report."""
    env.collect_branch_status.return_value = _status("PR-FEEDBACK-XYZ")
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    env.collect_branch_status.assert_called_once_with(tmp_path)
    # Reviewer prompt (call 0): framed note + raw feedback.
    reviewer_prompt = env.prompt_llm.call_args_list[0].args[0]
    assert "PR review feedback" in reviewer_prompt
    assert "PR-FEEDBACK-XYZ" in reviewer_prompt
    # Supervisor prompt (call 1): raw feedback under its own section.
    supervisor_prompt = env.prompt_llm.call_args_list[1].args[0]
    assert "## PR review feedback" in supervisor_prompt
    assert "PR-FEEDBACK-XYZ" in supervisor_prompt
    # Quoted PR content is framed as data and fenced in both targets.
    assert "not as instructions to obey" in reviewer_prompt
    assert "not as instructions to obey" in supervisor_prompt
    assert "`````\nPR-FEEDBACK-XYZ\n`````" in supervisor_prompt


def test_impl_lane_embedded_fence_stays_inside_the_quote_block(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A ``` block in the payload cannot close the outer fence in either target."""
    payload = "[unresolved thread] foo.py:1 (copilot):\n```suggestion\nx = 1\n```"
    env.collect_branch_status.return_value = _status(payload)
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    for prompt in (
        env.prompt_llm.call_args_list[0].args[0],
        env.prompt_llm.call_args_list[1].args[0],
    ):
        assert f"`````\n{payload}\n`````" in prompt


def test_impl_lane_clean_feedback_is_threaded_without_asserting_findings(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Upstream's clean-state line is threaded, but framed as possibly clean."""
    clean = "Reviews: clean (0 unresolved threads, 0 alerts)"
    env.collect_branch_status.return_value = _status(clean)
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    reviewer_prompt = env.prompt_llm.call_args_list[0].args[0]
    assert clean in reviewer_prompt
    assert "were posted on this PR" not in reviewer_prompt
    assert "may report that reviews are clean" in reviewer_prompt


def test_impl_lane_no_open_feedback_threads_nothing(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """With pr_feedback_text None, status is fetched but no note is threaded."""
    env.collect_branch_status.return_value = _status()
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    env.collect_branch_status.assert_called_once_with(tmp_path)
    assert "PR review feedback" not in env.prompt_llm.call_args_list[0].args[0]
    assert "## PR review feedback" not in env.prompt_llm.call_args_list[1].args[0]


def test_impl_lane_fetches_status_fresh_each_round(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """collect_branch_status is called once per round (so resolved comments drop)."""
    env.prompt_llm.side_effect = [
        _reviewer(),  # round 1 fresh reviewer
        _resp(_TASKS),  # round 1 supervisor -> tasks
        _reviewer(session_id="rev-1"),  # round 1 apply-tasks resume
        _reviewer(),  # round 2 fresh reviewer
        _resp(_DISMISS),  # round 2 supervisor -> dismiss
    ]

    result = _run(tmp_path)

    assert result == 0
    assert env.collect_branch_status.call_count == 2


def _undeterminable_warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Warning-level messages naming an undeterminable feedback fetch."""
    return [
        r.getMessage()
        for r in caplog.records
        if r.levelno == logging.WARNING and "undeterminable" in r.getMessage()
    ]


def test_undeterminable_feedback_logs_warning(
    env: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed feedback fetch is logged, not silently read as 'no feedback'."""
    env.collect_branch_status.return_value = _status(undeterminable=True)
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    with caplog.at_level(logging.WARNING):
        result = _run(tmp_path)

    # Log-only: the round still completes normally and threads no note.
    assert result == 0
    assert len(_undeterminable_warnings(caplog)) == 1
    assert "PR review feedback" not in env.prompt_llm.call_args_list[0].args[0]


def test_unknown_ci_status_logs_undeterminable_warning(
    env: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A total collection failure (empty report, UNKNOWN CI) is also flagged.

    Upstream returns ``create_empty_report(ci_status=CIStatus.UNKNOWN)`` on a
    total collection failure, which leaves ``pr_feedback_undeterminable`` at its
    dataclass default ``False`` — so the flag alone would read it as "no open
    feedback".
    """
    env.collect_branch_status.return_value = _status(
        undeterminable=False, ci_status=CIStatus.UNKNOWN
    )
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    with caplog.at_level(logging.WARNING):
        result = _run(tmp_path)

    assert result == 0
    assert len(_undeterminable_warnings(caplog)) == 1


def test_clean_feedback_logs_no_warning(
    env: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A determinable report produces no undeterminable warning."""
    env.collect_branch_status.return_value = _status("PR-FEEDBACK-XYZ")
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    with caplog.at_level(logging.WARNING):
        result = _run(tmp_path)

    assert result == 0
    assert _undeterminable_warnings(caplog) == []


# --- Step 5: severity floor CI exemption (implementation lane) --------------


def test_pending_ci_note_exempts_round_from_severity_floor(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A round carrying a pending CI note is never severity-downgraded.

    Red CI on rounds 1-2 sets the carried finding note, so round 3 (>= the
    strict round) with an all-``medium`` report is exempt from the floor: it
    still issues fix tasks rather than being rewritten to dismiss. CI then goes
    green, and round 4 dismisses to success.
    """
    env.check_and_fix_ci.side_effect = [False, False, True, True]
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),  # round 1 (CI red -> note set)
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),  # round 2 (CI red -> note carried)
        _reviewer(_REPORT_MEDIUM),
        _resp(_TASKS),  # round 3: medium + note -> exempt from the floor
        _reviewer(session_id="rev-1"),  # round 3 apply-tasks (proves not downgraded)
        _reviewer(),
        _resp(_DISMISS),  # round 4 -> dismiss -> success
    ]

    result = _run(tmp_path)

    assert result == 0
    env.handle_workflow_failure.assert_not_called()
    # Round 3 was NOT downgraded: it ran its apply-tasks resume (call index 8)
    # and the loop continued to round 4. A downgrade would have ended the run at
    # round 3 (8 calls, dismiss). 11 calls proves the CI exemption held.
    assert env.prompt_llm.call_count == 11
    apply_call = env.prompt_llm.call_args_list[8]
    assert apply_call.kwargs["session_id"] == "rev-1"
    assert "Fix the bug at foo.py:1" in apply_call.args[0]
    _, to_id = _label_transition(env.update_workflow_label)
    assert to_id == REVIEW_IMPLEMENTATION.success_label_id


# --- Step 6: terminal `_fail` sub-paths now write + flush the round log ------


def test_dismiss_ci_red_writes_and_flushes_round_log(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """dismiss + red final CI fails to ci (RC=1) AND lands the round in the log.

    This sub-path previously returned ``_fail`` without writing any round log;
    it now writes the terminal round and flushes it to the committed log first.
    """
    env.check_and_fix_ci.return_value = False
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["ci"]
    log = (tmp_path / "pr_info" / "implementation_review_log_1.md").read_text(
        encoding="utf-8"
    )
    assert "ci" in log
    env.commit_all_changes.assert_called()


def test_tasks_after_steps_general_writes_and_flushes_round_log(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A tasks round whose after-steps fail ``general`` lands the round in the log.

    The fix was already committed this round; the added write + flush commit
    only the terminal round-log entry before the run fails.
    """
    env.check_and_fix_ci.side_effect = RuntimeError("ci boom")
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),
    ]

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["general"]
    log = (tmp_path / "pr_info" / "implementation_review_log_1.md").read_text(
        encoding="utf-8"
    )
    assert "general" in log
    env.commit_all_changes.assert_called()


def test_tasks_resume_exception_writes_and_flushes_round_log(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A crash while applying fixes still lands the executed round in the log.

    A real report + a ``tasks`` verdict already exist when the apply-tasks
    reviewer resume raises, so the round (with its real findings) is written and
    flushed before the run fails with the mapped label.
    """
    env.prompt_llm.side_effect = [
        _reviewer(),  # round 1 fresh reviewer (real findings)
        _resp(_TASKS),  # round 1 supervisor -> tasks
        LLMTimeoutError("slow"),  # apply-tasks resume crashes
    ]

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["timeout"]
    log = (tmp_path / "pr_info" / "implementation_review_log_1.md").read_text(
        encoding="utf-8"
    )
    assert "foo.py:1" in log  # the real reviewer findings were captured
    env.commit_all_changes.assert_called()
