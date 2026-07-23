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
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflows.review import core
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION, REVIEW_PLAN

# --- verdict payloads -------------------------------------------------------

_DISMISS = '```json\n{"decision": "dismiss"}\n```'
_TASKS = '```json\n{"decision": "tasks", "tasks": ["Fix the bug at foo.py:1"]}\n```'

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
    """Patch every external the core loop + after-steps touch; expose the mocks."""
    mocks = SimpleNamespace()

    mocks.prompt_llm = MagicMock(name="prompt_llm")
    monkeypatch.setattr(core, "prompt_llm", mocks.prompt_llm)

    monkeypatch.setattr(core, "prepare_llm_environment", MagicMock(return_value={}))

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

    # After-steps externals: default to a clean rebase + green CI + a base branch.
    mocks.detect_base_branch = MagicMock(return_value="main")
    monkeypatch.setattr(core, "detect_base_branch", mocks.detect_base_branch)
    mocks.attempt_rebase_and_push = MagicMock(return_value=True)
    monkeypatch.setattr(core, "_attempt_rebase_and_push", mocks.attempt_rebase_and_push)
    mocks.check_and_fix_ci = MagicMock(return_value=True)
    monkeypatch.setattr(core, "check_and_fix_ci", mocks.check_and_fix_ci)

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
    source = inspect.getsource(core._after_steps)
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
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["mcp"]


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
    """Red CI on every tasks round hits the cap with the ci label, not rounds."""
    env.check_and_fix_ci.return_value = False
    per_round = [_reviewer(), _resp(_TASKS), _reviewer(session_id="rev-1")]
    env.prompt_llm.side_effect = per_round * core.REVIEW_MAX_ROUNDS

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    # Open CI finding at the cap wins over the plain rounds reason (17f-ci).
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["ci"]


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
