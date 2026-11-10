"""Tests for the check stage of process_single_task."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.constants import BLOCKED_FILE
from mcp_coder.workflows.implement.check_loop import CheckOutcome
from mcp_coder.workflows.implement.task_processing import process_single_task
from tests.workflows.implement.test_task_processing import _make_llm_response

_TP = "mcp_coder.workflows.implement.task_processing"


@dataclass
class _Mocks:
    """Patched collaborators of process_single_task."""

    check: MagicMock
    formatters: MagicMock
    commit: MagicMock
    push: MagicMock


@pytest.fixture(name="mocks")
def _mocks_fixture() -> Iterator[_Mocks]:
    """Patch everything but the check stage; files changed, task ticked."""
    with (
        patch(f"{_TP}.get_incomplete_tasks", return_value=["Step 3: Task"]),
        patch(f"{_TP}._count_incomplete_tasks", return_value=0),
        patch(f"{_TP}.get_prompt", return_value="Template"),
        patch(f"{_TP}.prompt_llm", return_value=_make_llm_response("Done")),
        patch(f"{_TP}.store_session"),
        patch(
            f"{_TP}.get_full_status",
            return_value={"staged": ["a.py"], "modified": [], "untracked": []},
        ),
        patch(f"{_TP}.check_and_fix_mypy", return_value=CheckOutcome("clean")) as check,
        patch(f"{_TP}.run_formatters", return_value=True) as formatters,
        patch(f"{_TP}.commit_changes", return_value=True) as commit,
        patch(f"{_TP}.push_changes", return_value=True) as push,
    ):
        yield _Mocks(check, formatters, commit, push)


class TestProcessSingleTaskChecks:
    """process_single_task maps the check loop's outcome."""

    @pytest.mark.parametrize("status", ["clean", "cap"])
    def test_clean_and_cap_commit_and_complete(
        self, mocks: _Mocks, tmp_path: Path, status: Any
    ) -> None:
        """Findings left at the cap do not fail the task."""
        mocks.check.return_value = CheckOutcome(status, "x")

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is True
        assert outcome.reason == "completed"
        mocks.formatters.assert_called_once()
        mocks.commit.assert_called_once()
        mocks.push.assert_called_once()

    @pytest.mark.parametrize(
        "status,detail",
        [
            ("error", "check@quick: tool crashed"),
            ("blocked", "cannot fix"),
            ("timeout", "marker text"),
            ("mcp_unavailable", ""),
        ],
    )
    def test_abort_statuses_fail_without_commit(
        self, mocks: _Mocks, tmp_path: Path, status: Any, detail: str
    ) -> None:
        """Every other status becomes the same reason, detail kept, no commit."""
        mocks.check.return_value = CheckOutcome(status, detail)

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == status
        assert outcome.detail == detail
        assert outcome.checks_failed is True
        mocks.formatters.assert_not_called()
        mocks.commit.assert_not_called()
        mocks.push.assert_not_called()

    @pytest.mark.parametrize("status", ["clean", "cap"])
    def test_marker_left_by_checks_is_blocked(
        self, mocks: _Mocks, tmp_path: Path, status: Any
    ) -> None:
        """A marker read by the safety net after the loop wins over its result."""

        def _writes_marker(*_args: Any, **_kwargs: Any) -> CheckOutcome:
            (tmp_path / "pr_info").mkdir(exist_ok=True)
            (tmp_path / BLOCKED_FILE).write_text("stuck on mypy", encoding="utf-8")
            return CheckOutcome(status)

        mocks.check.side_effect = _writes_marker

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "blocked"
        assert outcome.detail == "stuck on mypy"
        assert outcome.checks_failed is True
        mocks.commit.assert_not_called()
        assert not (tmp_path / BLOCKED_FILE).exists()

    def test_success_keeps_checks_failed_false(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """A completed task is not a check abort."""
        assert process_single_task(tmp_path, "claude").checks_failed is False

    def test_empty_main_response_is_not_a_check_abort(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """An empty response from the main LLM call keeps checks_failed False."""
        with patch(f"{_TP}.prompt_llm", return_value=_make_llm_response("")):
            outcome = process_single_task(tmp_path, "claude")

        assert outcome.reason == "error"
        assert outcome.checks_failed is False
        mocks.check.assert_not_called()
        mocks.commit.assert_not_called()

    def test_blocked_main_call_is_not_a_check_abort(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """A marker from the main LLM call keeps checks_failed False."""

        def _blocks(*_args: Any, **_kwargs: Any) -> Any:
            (tmp_path / "pr_info").mkdir(exist_ok=True)
            (tmp_path / BLOCKED_FILE).write_text("need input", encoding="utf-8")
            return _make_llm_response("Done")

        with patch(f"{_TP}.prompt_llm", side_effect=_blocks):
            outcome = process_single_task(tmp_path, "claude")

        assert outcome.reason == "blocked"
        assert outcome.checks_failed is False
        mocks.check.assert_not_called()
        mocks.commit.assert_not_called()

    def test_marker_cleared_when_check_raises(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """The safety net runs even if the loop raises unexpectedly."""

        def _raises(*_args: Any, **_kwargs: Any) -> CheckOutcome:
            (tmp_path / "pr_info").mkdir(exist_ok=True)
            (tmp_path / BLOCKED_FILE).write_text("stuck", encoding="utf-8")
            raise RuntimeError("boom")

        mocks.check.side_effect = _raises

        with pytest.raises(RuntimeError):
            process_single_task(tmp_path, "claude")

        assert not (tmp_path / BLOCKED_FILE).exists()

    @pytest.mark.parametrize("check_type_hints", [True, False])
    def test_forwards_entry_and_check_type_hints(
        self, mocks: _Mocks, tmp_path: Path, check_type_hints: bool
    ) -> None:
        """The loop always runs; check_type_hints is its filter, not a gate."""
        process_single_task(tmp_path, "claude", check_type_hints=check_type_hints)

        mocks.check.assert_called_once()
        args = mocks.check.call_args
        assert args.args[:3] == (tmp_path, 3, "claude")
        assert args.kwargs["entry"] == "implement_task"
        assert args.kwargs["check_type_hints"] is check_type_hints
