"""Tests for the rescue commit on check-stage aborts in run_implement_workflow."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.pyproject_config import ImplementConfig
from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.implement.check_loop import CheckOutcome
from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.task_processing import TaskOutcome

_CORE = "mcp_coder.workflows.implement.core"
_SUFFIX = " — rescue commit: pushed abc1234"


@dataclass
class _Mocks:
    """Patched collaborators of run_implement_workflow."""

    task: MagicMock
    check: MagicMock
    rescue: MagicMock
    fail: MagicMock


@pytest.fixture(name="mocks")
def _mocks_fixture() -> Iterator[_Mocks]:
    """One completed task, then the final check; everything else succeeds."""
    with (
        patch(f"{_CORE}.check_git_clean", return_value=True),
        patch(f"{_CORE}.check_main_branch", return_value=True),
        patch(f"{_CORE}.check_prerequisites", return_value=True),
        patch(f"{_CORE}._attempt_rebase_and_push", return_value=RebaseOutcome("ok")),
        patch(f"{_CORE}.check_formatter_config", return_value=None),
        patch(
            f"{_CORE}.get_implement_config",
            return_value=ImplementConfig(check_type_hints=True),
        ),
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
        patch(
            f"{_CORE}.check_and_fix_mypy", return_value=CheckOutcome("clean")
        ) as check,
        patch(f"{_CORE}.rescue_commit", return_value="pushed abc1234") as rescue,
        patch(f"{_CORE}.run_formatters", return_value=True),
        patch(
            f"{_CORE}.get_full_status",
            return_value={"staged": [], "modified": [], "untracked": []},
        ),
        patch(f"{_CORE}.run_finalisation", return_value=True),
        patch(f"{_CORE}.get_current_branch_name", return_value="feat"),
        patch(f"{_CORE}.check_and_fix_ci", return_value=True),
        patch(f"{_CORE}._fail", return_value=1) as fail,
    ):
        yield _Mocks(task, check, rescue, fail)


def _failure(mocks: _Mocks) -> tuple[str, str, str]:
    """Return (reason, stage, message) of the single _fail call."""
    mocks.fail.assert_called_once()
    call = mocks.fail.call_args
    return call.args[1], call.kwargs["stage"], call.kwargs["message"]


_TASK_REASONS = [
    ("error", "general"),
    ("blocked", "blocked"),
    ("timeout", "timeout"),
    ("mcp_unavailable", "mcp_unavailable"),
]


class TestTaskCheckAbort:
    """Per-task outcomes are rescued only when they come from the check stage."""

    @pytest.mark.parametrize("task_reason,fail_reason", _TASK_REASONS)
    def test_check_abort_is_rescued(
        self, mocks: _Mocks, tmp_path: Path, task_reason: str, fail_reason: str
    ) -> None:
        """A check-stage abort commits first; the reason is unchanged."""
        mocks.task.side_effect = [
            TaskOutcome(False, task_reason, "detail", checks_failed=True)
        ]

        assert run_implement_workflow(tmp_path, "claude") == 1

        mocks.rescue.assert_called_once_with(tmp_path, fail_reason)
        reason, stage, message = _failure(mocks)
        assert reason == fail_reason
        assert stage == "Task implementation"
        assert message.endswith(_SUFFIX)
        mocks.check.assert_not_called()

    @pytest.mark.parametrize("task_reason,fail_reason", _TASK_REASONS)
    def test_other_aborts_are_not_rescued(
        self, mocks: _Mocks, tmp_path: Path, task_reason: str, fail_reason: str
    ) -> None:
        """Exits from the main LLM call commit nothing."""
        mocks.task.side_effect = [TaskOutcome(False, task_reason, "detail")]

        assert run_implement_workflow(tmp_path, "claude") == 1

        mocks.rescue.assert_not_called()
        reason, _, message = _failure(mocks)
        assert reason == fail_reason
        assert "rescue commit" not in message


class TestFinalCheckAbort:
    """Every non-clean final check is rescued before failing."""

    def test_cap_is_checks_exhausted(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Findings at the cap are rescued as checks_exhausted."""
        mocks.check.return_value = CheckOutcome("cap", "2 left")

        assert run_implement_workflow(tmp_path, "claude") == 1

        mocks.rescue.assert_called_once_with(tmp_path, "checks_exhausted")
        reason, stage, message = _failure(mocks)
        assert reason == "checks_exhausted"
        assert stage == "Final mypy check"
        assert message.endswith(_SUFFIX)

    @pytest.mark.parametrize(
        "status,fail_reason",
        [
            ("error", "general"),
            ("blocked", "blocked"),
            ("timeout", "timeout"),
            ("mcp_unavailable", "mcp_unavailable"),
        ],
    )
    def test_aborts_are_rescued(
        self, mocks: _Mocks, tmp_path: Path, status: Any, fail_reason: str
    ) -> None:
        """Each abort status keeps its reason after the rescue."""
        mocks.check.return_value = CheckOutcome(status, "detail")

        assert run_implement_workflow(tmp_path, "claude") == 1

        mocks.rescue.assert_called_once_with(tmp_path, fail_reason)
        reason, _, message = _failure(mocks)
        assert reason == fail_reason
        assert message.endswith(_SUFFIX)

    def test_failed_rescue_keeps_reason(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A failed rescue commit does not replace the original reason."""
        mocks.check.return_value = CheckOutcome("cap", "2 left")
        mocks.rescue.return_value = "commit failed: x"

        assert run_implement_workflow(tmp_path, "claude") == 1

        reason, _, message = _failure(mocks)
        assert reason == "checks_exhausted"
        assert message.endswith(" — rescue commit: commit failed: x")

    def test_config_error_is_general_with_message(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """A config ValueError surfaces as general with its message."""
        mocks.check.return_value = CheckOutcome("error", "bad toolkit config")

        assert run_implement_workflow(tmp_path, "claude") == 1

        assert _failure(mocks) == (
            "general",
            "Final mypy check",
            f"bad toolkit config{_SUFFIX}",
        )
