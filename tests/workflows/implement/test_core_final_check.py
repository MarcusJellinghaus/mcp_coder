"""Tests for the final check gate in run_implement_workflow."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.pyproject_config import ImplementConfig
from mcp_coder.workflow_steps.constants import BLOCKED_FILE
from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.implement.check_loop import MAX_FIX_TURNS, CheckOutcome
from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.task_processing import TaskOutcome

_CORE = "mcp_coder.workflows.implement.core"
_STAGE = "Final mypy check"
_SUFFIX = " — rescue commit: pushed abc1234"


@dataclass
class _Mocks:
    """Patched collaborators of run_implement_workflow."""

    check: MagicMock
    config: MagicMock
    fail: MagicMock
    formatters: MagicMock
    finalisation: MagicMock
    process: MagicMock


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
        ) as config,
        patch(f"{_CORE}.prepare_task_tracker"),
        patch(f"{_CORE}.log_progress_summary"),
        patch(f"{_CORE}.get_step_progress", return_value={}),
        patch(
            f"{_CORE}.process_task_with_retry",
            side_effect=[
                TaskOutcome(True, "completed"),
                TaskOutcome(False, "no_tasks"),
            ],
        ) as process,
        patch(f"{_CORE}.prepare_llm_environment", return_value={}),
        patch(
            f"{_CORE}.check_and_fix_mypy", return_value=CheckOutcome("clean")
        ) as check,
        patch(f"{_CORE}.rescue_commit", return_value="pushed abc1234"),
        patch(f"{_CORE}.run_formatters", return_value=True) as formatters,
        patch(
            f"{_CORE}.get_full_status",
            return_value={"staged": [], "modified": [], "untracked": []},
        ),
        patch(f"{_CORE}.run_finalisation", return_value=True) as finalisation,
        patch(f"{_CORE}.get_current_branch_name", return_value="feat"),
        patch(f"{_CORE}.check_and_fix_ci", return_value=True),
        patch(f"{_CORE}._fail", return_value=1) as fail,
    ):
        yield _Mocks(check, config, fail, formatters, finalisation, process)


def _failure(mocks: _Mocks) -> tuple[str, str, str]:
    """Return (reason, stage, message) of the single _fail call."""
    mocks.fail.assert_called_once()
    call = mocks.fail.call_args
    return call.args[1], call.kwargs["stage"], call.kwargs["message"]


class TestFinalCheckGate:
    """A non-clean final check fails the workflow."""

    def test_clean_continues(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A clean check formats and moves on to finalisation."""
        assert run_implement_workflow(tmp_path, "claude") == 0

        mocks.fail.assert_not_called()
        mocks.formatters.assert_called_once()
        mocks.finalisation.assert_called_once()
        assert mocks.check.call_args.kwargs["entry"] == "implement_final"

    def test_cap_is_checks_exhausted(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Findings at the cap fail as checks_exhausted, with the detail."""
        detail = f"fix.check: findings remain after {MAX_FIX_TURNS} fix turns"
        mocks.check.return_value = CheckOutcome("cap", detail)

        assert run_implement_workflow(tmp_path, "claude") == 1

        reason, stage, message = _failure(mocks)
        assert reason == "checks_exhausted"
        assert stage == _STAGE
        assert message == f"{detail}{_SUFFIX}"
        mocks.formatters.assert_not_called()
        mocks.finalisation.assert_not_called()

    def test_early_cap_message_keeps_real_turn_count(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """A cap before the third fix turn does not claim three fix turns."""
        detail = "fix.check: no usable fragment after 0 fix turns"
        mocks.check.return_value = CheckOutcome("cap", detail)

        assert run_implement_workflow(tmp_path, "claude") == 1

        reason, _stage, message = _failure(mocks)
        assert reason == "checks_exhausted"
        assert message == f"{detail}{_SUFFIX}"
        assert f"after {MAX_FIX_TURNS} fix turns" not in message

    def test_error_is_general_with_detail(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A config or tool error fails as general; the detail is the message."""
        mocks.check.return_value = CheckOutcome("error", "bad toolkit config")

        assert run_implement_workflow(tmp_path, "claude") == 1

        assert _failure(mocks) == ("general", _STAGE, f"bad toolkit config{_SUFFIX}")
        mocks.finalisation.assert_not_called()

    def test_blocked(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A blocked fix turn fails as blocked with the marker text."""
        mocks.check.return_value = CheckOutcome("blocked", "cannot fix")

        assert run_implement_workflow(tmp_path, "claude") == 1

        assert _failure(mocks) == ("blocked", _STAGE, f"cannot fix{_SUFFIX}")

    def test_marker_after_clean_is_blocked(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A marker read in the finally turns a clean result into blocked."""

        def _writes_marker(*_args: Any, **_kwargs: Any) -> CheckOutcome:
            (tmp_path / "pr_info").mkdir(exist_ok=True)
            (tmp_path / BLOCKED_FILE).write_text("gave up", encoding="utf-8")
            return CheckOutcome("clean")

        mocks.check.side_effect = _writes_marker

        assert run_implement_workflow(tmp_path, "claude") == 1

        assert _failure(mocks) == ("blocked", _STAGE, f"gave up{_SUFFIX}")
        assert not (tmp_path / BLOCKED_FILE).exists()
        mocks.formatters.assert_not_called()

    @pytest.mark.parametrize("status", ["timeout", "mcp_unavailable"])
    def test_llm_failures_keep_reason_and_marker(
        self, mocks: _Mocks, tmp_path: Path, status: Any
    ) -> None:
        """Typed LLM failures keep their reason; the marker text is appended."""
        mocks.check.return_value = CheckOutcome(status, "server hung")

        assert run_implement_workflow(tmp_path, "claude") == 1

        reason, stage, message = _failure(mocks)
        assert reason == status
        assert stage == _STAGE
        assert message.startswith("LLM failure during final mypy check")
        assert "server hung" in message

    @pytest.mark.parametrize("check_type_hints", [True, False])
    def test_forwards_check_type_hints(
        self, mocks: _Mocks, tmp_path: Path, check_type_hints: bool
    ) -> None:
        """check_type_hints from ImplementConfig reaches the loop as its filter."""
        mocks.config.return_value = ImplementConfig(check_type_hints=check_type_hints)

        run_implement_workflow(tmp_path, "claude")

        mocks.check.assert_called_once()
        assert mocks.check.call_args.kwargs["check_type_hints"] is check_type_hints


class TestFinalCheckWithoutCompletedTasks:
    """A re-run that finds every task ticked still runs the final check."""

    def test_runs_final_check(self, mocks: _Mocks, tmp_path: Path) -> None:
        """no_tasks on the first round still calls the implement_final check."""
        mocks.process.side_effect = None
        mocks.process.return_value = TaskOutcome(False, "no_tasks")

        assert run_implement_workflow(tmp_path, "claude") == 0

        mocks.check.assert_called_once()
        assert mocks.check.call_args.kwargs["entry"] == "implement_final"
        mocks.fail.assert_not_called()

    def test_cap_is_checks_exhausted(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Findings at the cap fail the re-run as checks_exhausted."""
        mocks.process.side_effect = None
        mocks.process.return_value = TaskOutcome(False, "no_tasks")
        mocks.check.return_value = CheckOutcome("cap", "fix.check: 2 left")

        assert run_implement_workflow(tmp_path, "claude") == 1

        reason, stage, _message = _failure(mocks)
        assert reason == "checks_exhausted"
        assert stage == _STAGE
        mocks.finalisation.assert_not_called()
