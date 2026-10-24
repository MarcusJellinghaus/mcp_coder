"""Tests for create_pr pre-creation steps."""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.create_pr.pre_creation import _rebase_if_needed

_MODULE = "mcp_coder.workflows.create_pr.pre_creation"
_PROJECT = Path("/test")


@dataclass
class _Mocks:
    branch: MagicMock
    base: MagicMock
    needs: MagicMock
    attempt: MagicMock


@pytest.fixture
def mocks() -> Iterator[_Mocks]:
    """Patch the git/rebase collaborators of ``_rebase_if_needed``."""
    with (
        patch(f"{_MODULE}.get_current_branch_name", return_value="feat") as branch,
        patch(f"{_MODULE}.detect_base_branch", return_value="main") as base,
        patch(f"{_MODULE}.needs_rebase") as needs,
        patch(
            f"{_MODULE}._attempt_rebase_and_push",
            return_value=RebaseOutcome(reason="ok", base_branch="main"),
        ) as attempt,
    ):
        yield _Mocks(branch=branch, base=base, needs=needs, attempt=attempt)


class TestRebaseIfNeeded:
    """Tests for _rebase_if_needed."""

    def test_rebases_when_behind(self, mocks: _Mocks) -> None:
        """Branch behind base → rebase-and-push runs once."""
        mocks.needs.return_value = (True, "behind by 2 commits")

        _rebase_if_needed(_PROJECT)

        mocks.base.assert_called_once_with(_PROJECT, current_branch="feat")
        mocks.needs.assert_called_once_with(_PROJECT, "main")
        mocks.attempt.assert_called_once_with(_PROJECT)

    def test_skips_when_up_to_date(self, mocks: _Mocks) -> None:
        """Up to date → no rebase."""
        mocks.needs.return_value = (False, "up to date")

        _rebase_if_needed(_PROJECT)

        mocks.attempt.assert_not_called()

    def test_needs_rebase_error_logs_warning(
        self, mocks: _Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An ``error:`` reason is logged as a warning and skipped."""
        mocks.needs.return_value = (False, "error: fetch failed")

        with caplog.at_level(logging.WARNING):
            _rebase_if_needed(_PROJECT)

        mocks.attempt.assert_not_called()
        assert "error: fetch failed" in caplog.text

    def test_no_base_branch_skips(
        self, mocks: _Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Base branch unknown → needs_rebase not called, warning logged."""
        mocks.base.return_value = None

        with caplog.at_level(logging.WARNING):
            _rebase_if_needed(_PROJECT)

        mocks.needs.assert_not_called()
        mocks.attempt.assert_not_called()
        assert "base branch" in caplog.text

    def test_rebase_conflict_returns_normally(self, mocks: _Mocks) -> None:
        """A failed rebase outcome is logged only."""
        mocks.needs.return_value = (True, "behind")
        mocks.attempt.return_value = RebaseOutcome(
            reason="conflict", base_branch="main"
        )

        _rebase_if_needed(_PROJECT)

        mocks.attempt.assert_called_once_with(_PROJECT)

    def test_exception_is_swallowed(
        self, mocks: _Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An exception from needs_rebase never escapes."""
        mocks.needs.side_effect = RuntimeError("git exploded")

        with caplog.at_level(logging.WARNING):
            _rebase_if_needed(_PROJECT)

        mocks.attempt.assert_not_called()
        assert "git exploded" in caplog.text
