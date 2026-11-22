"""Tests for the auth failure routing in run_implement_workflow."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMAuthError, LLMTimeoutError
from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.implement.check_loop import CheckOutcome
from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.failure_reporting import _fail
from mcp_coder.workflows.implement.task_processing import TaskOutcome
from tests.logged_out_capture import AUTH_HINT, AUTH_MESSAGE

_CORE = "mcp_coder.workflows.implement.core"
_REPORTING = "mcp_coder.workflows.implement.failure_reporting"
_DETAIL = f"LLMAuthError: {AUTH_MESSAGE}"


@dataclass
class _Mocks:
    """Patched collaborators of run_implement_workflow."""

    task: MagicMock
    check: MagicMock
    rescue: MagicMock
    finalise: MagicMock
    ci: MagicMock
    fail: MagicMock
    handle: MagicMock


@pytest.fixture(name="mocks")
def _mocks_fixture() -> Iterator[_Mocks]:
    """One completed task, then the final check; everything else succeeds."""
    with (
        patch(f"{_CORE}.check_git_clean", return_value=True),
        patch(f"{_CORE}.check_main_branch", return_value=True),
        patch(f"{_CORE}.check_prerequisites", return_value=True),
        patch(f"{_CORE}._attempt_rebase_and_push", return_value=RebaseOutcome("ok")),
        patch(f"{_CORE}.check_formatter_config", return_value=None),
        patch(f"{_CORE}.prepare_task_tracker"),
        patch(f"{_CORE}.log_progress_summary"),
        patch(f"{_CORE}.get_step_progress", return_value={}),
        patch(
            f"{_CORE}.process_task_with_retry",
            side_effect=[
                TaskOutcome(True, "completed"),
                TaskOutcome(False, "no_tasks"),
            ],
        ) as task,
        patch(f"{_CORE}.prepare_llm_environment", return_value={}),
        patch(f"{_CORE}.check_and_fix", return_value=CheckOutcome("clean")) as check,
        patch(f"{_CORE}.rescue_commit", return_value="pushed abc1234") as rescue,
        patch(f"{_CORE}.run_formatters", return_value=True),
        patch(
            f"{_CORE}.get_full_status",
            return_value={"staged": [], "modified": [], "untracked": []},
        ),
        patch(f"{_CORE}.run_finalisation", return_value=True) as finalise,
        patch(f"{_CORE}.get_current_branch_name", return_value="feat"),
        patch(f"{_CORE}.check_and_fix_ci", return_value=True) as ci,
        patch(f"{_CORE}._fail", wraps=_fail) as fail,
        patch(f"{_REPORTING}.get_diff_stat", return_value=""),
        patch(f"{_REPORTING}.handle_workflow_failure") as handle,
    ):
        yield _Mocks(task, check, rescue, finalise, ci, fail, handle)


def _failure(mocks: _Mocks) -> tuple[str, str, str]:
    """Return (reason, stage, message) of the single _fail call."""
    mocks.fail.assert_called_once()
    call = mocks.fail.call_args
    return call.args[1], call.kwargs["stage"], call.kwargs["message"]


def _label(mocks: _Mocks) -> str:
    """Return the label category handed to handle_workflow_failure."""
    mocks.handle.assert_called_once()
    category: str = mocks.handle.call_args.kwargs["failure"].category
    return category


class TestTaskAuth:
    """Auth outcomes from process_task_with_retry stop the loop at once."""

    def test_task_call_auth_fails_without_rescue(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """An auth failure of the task call fails with its error text."""
        mocks.task.side_effect = [TaskOutcome(False, "auth", _DETAIL)]

        assert run_implement_workflow(tmp_path, "claude") == 1

        assert mocks.task.call_count == 1
        mocks.rescue.assert_not_called()
        mocks.check.assert_not_called()
        reason, stage, message = _failure(mocks)
        assert reason == "auth"
        assert stage == "Task implementation"
        assert AUTH_HINT in message
        assert "rescue commit" not in message
        assert _label(mocks) == "implementing_failed"

    def test_fix_turn_auth_is_rescued(self, mocks: _Mocks, tmp_path: Path) -> None:
        """An auth failure in the per-task fix turn commits first."""
        mocks.task.side_effect = [
            TaskOutcome(False, "auth", _DETAIL, checks_failed=True)
        ]

        assert run_implement_workflow(tmp_path, "claude") == 1

        assert mocks.task.call_count == 1
        mocks.rescue.assert_called_once_with(tmp_path, "auth")
        reason, stage, message = _failure(mocks)
        assert reason == "auth"
        assert stage == "Task implementation"
        assert AUTH_HINT in message
        assert message.endswith(" — rescue commit: pushed abc1234")
        mocks.check.assert_not_called()


class TestFinalCheckAuth:
    """An auth failure in a final-check fix turn is rescued, then fails."""

    def test_final_check_auth_is_rescued(self, mocks: _Mocks, tmp_path: Path) -> None:
        """The error text is the message; no agent-reported suffix is invented."""
        mocks.check.return_value = CheckOutcome("auth", _DETAIL)

        assert run_implement_workflow(tmp_path, "claude") == 1

        mocks.rescue.assert_called_once_with(tmp_path, "auth")
        reason, stage, message = _failure(mocks)
        assert reason == "auth"
        assert stage == "Final checks"
        assert message.startswith(_DETAIL)
        assert "agent reported" not in message
        assert _label(mocks) == "implementing_failed"

    def test_final_check_auth_keeps_marker(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A blocked marker carried in the detail survives into the message."""
        detail = f"{_DETAIL} (agent reported: stuck)"
        mocks.check.return_value = CheckOutcome("auth", detail)

        assert run_implement_workflow(tmp_path, "claude") == 1

        _, _, message = _failure(mocks)
        assert message.startswith(detail)


class TestFinalisationAndCiAuth:
    """Auth failures at finalisation and the CI step fail with the error text."""

    def test_finalisation_auth_fails(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Finalisation auth is a deliberate failure, not the Crashed net."""
        mocks.finalise.side_effect = LLMAuthError(AUTH_MESSAGE)

        assert run_implement_workflow(tmp_path, "claude") == 1

        reason, stage, message = _failure(mocks)
        assert reason == "auth"
        assert stage == "Finalisation"
        assert AUTH_HINT in message
        mocks.ci.assert_not_called()
        mocks.rescue.assert_not_called()
        assert _label(mocks) == "implementing_failed"

    def test_ci_auth_fails(self, mocks: _Mocks, tmp_path: Path) -> None:
        """CI analysis or fix-phase auth fails at the CI pipeline analysis stage."""
        mocks.ci.side_effect = LLMAuthError(AUTH_MESSAGE)

        assert run_implement_workflow(tmp_path, "claude") == 1

        reason, stage, message = _failure(mocks)
        assert reason == "auth"
        assert stage == "CI pipeline analysis"
        assert AUTH_HINT in message
        assert _label(mocks) == "implementing_failed"

    def test_ci_timeout_message_unchanged(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A CI-analysis timeout keeps its generic message."""
        mocks.ci.side_effect = LLMTimeoutError("timed out")

        assert run_implement_workflow(tmp_path, "claude") == 1

        reason, stage, message = _failure(mocks)
        assert reason == "timeout"
        assert stage == "CI pipeline analysis"
        assert message == "LLM failure during CI failure analysis"
