"""Tests for create_pr pre-creation steps."""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.create_pr.pre_creation import (
    _find_open_pr,
    _rebase_if_needed,
    _resume_cleanup,
)

_MODULE = "mcp_coder.workflows.create_pr.pre_creation"
_PROJECT = Path("/test")


@dataclass
class _Mocks:
    branch: MagicMock
    base: MagicMock
    needs: MagicMock
    attempt: MagicMock
    sha: MagicMock
    reset: MagicMock


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
        patch(f"{_MODULE}.get_latest_commit_sha", return_value="before") as sha,
        patch(f"{_MODULE}._reset_hard", return_value=True) as reset,
    ):
        yield _Mocks(
            branch=branch,
            base=base,
            needs=needs,
            attempt=attempt,
            sha=sha,
            reset=reset,
        )


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
        mocks.reset.assert_not_called()

    def test_push_failed_restores_head(self, mocks: _Mocks) -> None:
        """Rebased locally but push failed → reset to the pre-rebase HEAD."""
        mocks.needs.return_value = (True, "behind")
        mocks.attempt.return_value = RebaseOutcome(
            reason="push_failed", base_branch="main"
        )

        _rebase_if_needed(_PROJECT)

        mocks.reset.assert_called_once_with(_PROJECT, "before")

    def test_ok_rebase_keeps_head(self, mocks: _Mocks) -> None:
        """A pushed rebase is not undone."""
        mocks.needs.return_value = (True, "behind")

        _rebase_if_needed(_PROJECT)

        mocks.reset.assert_not_called()

    def test_exception_is_swallowed(
        self, mocks: _Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An exception from needs_rebase never escapes."""
        mocks.needs.side_effect = RuntimeError("git exploded")

        with caplog.at_level(logging.WARNING):
            _rebase_if_needed(_PROJECT)

        mocks.attempt.assert_not_called()
        assert "git exploded" in caplog.text


class TestFindOpenPr:
    """Tests for _find_open_pr."""

    @patch(f"{_MODULE}.PullRequestManager")
    @patch(f"{_MODULE}.get_current_branch_name", return_value="feat")
    def test_returns_first_open_pr(
        self, _mock_branch: MagicMock, mock_manager: MagicMock
    ) -> None:
        """An open PR for the branch is returned."""
        pr = MagicMock()
        mock_manager.return_value.find_pull_request_by_head.return_value = [pr]

        assert _find_open_pr(_PROJECT) is pr
        mock_manager.return_value.find_pull_request_by_head.assert_called_once_with(
            "feat"
        )

    @patch(f"{_MODULE}.PullRequestManager")
    @patch(f"{_MODULE}.get_current_branch_name", return_value="feat")
    def test_no_open_pr_returns_none(
        self, _mock_branch: MagicMock, mock_manager: MagicMock
    ) -> None:
        """No open PR → None."""
        mock_manager.return_value.find_pull_request_by_head.return_value = []

        assert _find_open_pr(_PROJECT) is None

    @patch(f"{_MODULE}.PullRequestManager")
    @patch(f"{_MODULE}.get_current_branch_name", return_value=None)
    def test_unknown_branch_returns_none(
        self, _mock_branch: MagicMock, mock_manager: MagicMock
    ) -> None:
        """Branch unknown → None, no GitHub lookup."""
        assert _find_open_pr(_PROJECT) is None
        mock_manager.assert_not_called()

    @patch(f"{_MODULE}.PullRequestManager")
    @patch(f"{_MODULE}.get_current_branch_name", return_value="feat")
    def test_lookup_error_returns_none(
        self,
        _mock_branch: MagicMock,
        mock_manager: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A lookup exception is logged as a warning and never escapes."""
        mock_manager.return_value.find_pull_request_by_head.side_effect = RuntimeError(
            "api down"
        )

        with caplog.at_level(logging.WARNING):
            assert _find_open_pr(_PROJECT) is None

        assert "api down" in caplog.text


class TestResumeCleanup:
    """Tests for _resume_cleanup."""

    @patch(f"{_MODULE}.check_git_clean")
    def test_no_pr_info_does_nothing(
        self, mock_clean: MagicMock, tmp_path: Path
    ) -> None:
        """No pr_info/ → None, cleanup not run."""
        cleanup = MagicMock()

        assert _resume_cleanup(tmp_path, cleanup) is None

        cleanup.assert_not_called()
        mock_clean.assert_not_called()

    @patch(f"{_MODULE}.check_git_clean", return_value=True)
    def test_pr_info_clean_runs_cleanup(
        self, _mock_clean: MagicMock, tmp_path: Path
    ) -> None:
        """pr_info/ present and clean tree → cleanup's result is returned."""
        (tmp_path / "pr_info").mkdir()
        cleanup = MagicMock(return_value=("push", "rejected"))

        assert _resume_cleanup(tmp_path, cleanup) == ("push", "rejected")

        cleanup.assert_called_once_with(tmp_path)

    @patch(f"{_MODULE}.check_git_clean", return_value=False)
    def test_pr_info_dirty_tree_fails(
        self, _mock_clean: MagicMock, tmp_path: Path
    ) -> None:
        """pr_info/ present and dirty tree → resume_cleanup failure, no cleanup."""
        (tmp_path / "pr_info").mkdir()
        cleanup = MagicMock()

        result = _resume_cleanup(tmp_path, cleanup)

        assert result is not None
        assert result[0] == "resume_cleanup"
        cleanup.assert_not_called()
