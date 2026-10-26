"""Tests for preparing restart branches."""

from pathlib import Path
from typing import Any, NamedTuple
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflows.vscodeclaude.session_restart import (
    BranchPrepResult,
    _prepare_restart_branch,
)

_MODULE = "mcp_coder.workflows.vscodeclaude.session_restart"


class GitMocks(NamedTuple):
    """Mocks for the shim git functions used by _prepare_restart_branch."""

    fetch_remote: MagicMock
    checkout_branch: MagicMock
    pull: MagicMock


@pytest.fixture
def git_mocks(monkeypatch: pytest.MonkeyPatch) -> GitMocks:
    """Patch fetch/checkout/pull with succeeding mocks."""
    mocks = GitMocks(
        fetch_remote=MagicMock(return_value=True),
        checkout_branch=MagicMock(return_value=True),
        pull=MagicMock(
            return_value={
                "success": True,
                "error": None,
                "returncode": 0,
                "stderr": "",
            }
        ),
    )
    monkeypatch.setattr(f"{_MODULE}.fetch_remote", mocks.fetch_remote)
    monkeypatch.setattr(f"{_MODULE}.checkout_branch", mocks.checkout_branch)
    monkeypatch.setattr(f"{_MODULE}.pull", mocks.pull)
    return mocks


def _branch_manager(branch: str | None) -> Any:
    """Build a branch manager stub returning ``branch``."""
    return type(
        "MockBranchManager",
        (),
        {
            "get_branch_with_pr_fallback": lambda self, issue_number, repo_owner, repo_name: (
                branch
            ),
        },
    )()


class TestPrepareRestartBranch:
    """Tests for _prepare_restart_branch() helper."""

    def test_status_01_skips_branch_check(
        self, tmp_path: Path, git_mocks: GitMocks
    ) -> None:
        """status-01 doesn't require branch - returns success immediately."""
        mock_branch_manager = type("MockBranchManager", (), {})()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=123,
            repo_owner="test-owner",
            repo_name="test-repo",
        )

        assert result == BranchPrepResult(True, None, None)
        git_mocks.fetch_remote.assert_called_once_with(tmp_path)
        git_mocks.checkout_branch.assert_not_called()
        git_mocks.pull.assert_not_called()

    def test_status_04_no_branch_returns_skip(
        self, tmp_path: Path, git_mocks: GitMocks
    ) -> None:
        """status-04 without linked branch returns No branch skip."""
        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=_branch_manager(None),
            issue_number=123,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(False, "No branch", None)
        git_mocks.checkout_branch.assert_not_called()

    def test_status_07_dirty_returns_skip(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        git_mocks: GitMocks,
    ) -> None:
        """status-07 with dirty repo returns Dirty skip."""
        monkeypatch.setattr(f"{_MODULE}.get_folder_git_status", lambda folder: "Dirty")

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-07:code-review",
            branch_manager=_branch_manager("feat-branch"),
            issue_number=456,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(False, "Dirty", None)
        git_mocks.checkout_branch.assert_not_called()
        git_mocks.pull.assert_not_called()

    def test_status_04_clean_switches_branch(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        git_mocks: GitMocks,
    ) -> None:
        """status-04 with clean repo switches to linked branch."""
        monkeypatch.setattr(f"{_MODULE}.get_folder_git_status", lambda folder: "Clean")

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=_branch_manager("feat-123"),
            issue_number=123,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(True, None, "feat-123")
        git_mocks.checkout_branch.assert_called_once_with("feat-123", tmp_path)
        git_mocks.pull.assert_called_once_with(tmp_path)

    def test_git_checkout_failure_returns_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        git_mocks: GitMocks,
    ) -> None:
        """Git checkout failure returns Git error skip."""
        git_mocks.checkout_branch.return_value = False
        monkeypatch.setattr(f"{_MODULE}.get_folder_git_status", lambda folder: "Clean")

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=_branch_manager("feat-branch"),
            issue_number=123,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(False, "Git error", None)
        git_mocks.pull.assert_not_called()

    def test_git_pull_failure_returns_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        git_mocks: GitMocks,
    ) -> None:
        """Git pull failure returns Git error skip."""
        git_mocks.pull.return_value = {
            "success": False,
            "error": "git pull failed (exit 1)",
            "returncode": 1,
            "stderr": "conflict",
        }
        monkeypatch.setattr(f"{_MODULE}.get_folder_git_status", lambda folder: "Clean")

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=_branch_manager("feat-branch"),
            issue_number=123,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(False, "Git error", None)
        git_mocks.checkout_branch.assert_called_once_with("feat-branch", tmp_path)

    def test_git_fetch_failure_returns_error(
        self, tmp_path: Path, git_mocks: GitMocks
    ) -> None:
        """Git fetch failure returns Git error skip without checkout or pull."""
        git_mocks.fetch_remote.return_value = False

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=_branch_manager("feat-branch"),
            issue_number=123,
            repo_owner="test-owner",
            repo_name="test-repo",
        )

        assert result == BranchPrepResult(False, "Git error", None)
        git_mocks.checkout_branch.assert_not_called()
        git_mocks.pull.assert_not_called()

    def test_multi_branch_returns_skip(
        self, tmp_path: Path, git_mocks: GitMocks
    ) -> None:
        """Multiple branches (returns None) results in No branch skip."""
        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=_branch_manager(None),
            issue_number=123,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(False, "No branch", None)
