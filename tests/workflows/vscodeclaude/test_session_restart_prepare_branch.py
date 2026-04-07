"""Tests for preparing restart branches."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.subprocess_runner import CalledProcessError
from mcp_coder.workflows.vscodeclaude.session_restart import (
    BranchPrepResult,
    _prepare_restart_branch,
)


class TestPrepareRestartBranch:
    """Tests for _prepare_restart_branch() helper."""

    def test_status_01_skips_branch_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-01 doesn't require branch - returns success immediately."""
        # Mock git fetch to succeed
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            lambda cmd, options: type(
                "Result", (), {"stdout": "", "stderr": "", "return_code": 0}
            )(),
        )
        mock_branch_manager = type("MockBranchManager", (), {})()
        mock_branch_manager.get_linked_branches = lambda issue_number: []

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=123,
            repo_owner="test-owner",
            repo_name="test-repo",
        )

        assert result == BranchPrepResult(True, None, None)

    def test_status_04_no_branch_returns_skip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-04 without linked branch returns No branch skip."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            lambda cmd, options: type(
                "Result", (), {"stdout": "", "stderr": "", "return_code": 0}
            )(),
        )
        mock_branch_manager = type(
            "MockBranchManager",
            (),
            {
                "get_branch_with_pr_fallback": lambda self, issue_number, repo_owner, repo_name: None,
            },
        )()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(False, "No branch", None)

    def test_status_07_dirty_returns_skip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-07 with dirty repo returns Dirty skip."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            lambda cmd, options: type(
                "Result", (), {"stdout": "", "stderr": "", "return_code": 0}
            )(),
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.get_folder_git_status",
            lambda folder: "Dirty",
        )
        mock_branch_manager = type(
            "MockBranchManager",
            (),
            {
                "get_branch_with_pr_fallback": lambda self, issue_number, repo_owner, repo_name: "feat-branch",
            },
        )()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-07:code-review",
            branch_manager=mock_branch_manager,
            issue_number=456,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(False, "Dirty", None)

    def test_status_04_clean_switches_branch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-04 with clean repo switches to linked branch."""
        execute_calls: list[Any] = []

        def mock_execute(cmd: list[str], options: Any) -> Any:
            execute_calls.append(cmd)
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.get_folder_git_status",
            lambda folder: "Clean",
        )
        mock_branch_manager = type(
            "MockBranchManager",
            (),
            {
                "get_branch_with_pr_fallback": lambda self, issue_number, repo_owner, repo_name: "feat-123",
            },
        )()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(True, None, "feat-123")
        # Verify git checkout and pull were called
        assert any("checkout" in str(c) for c in execute_calls)
        assert any("pull" in str(c) for c in execute_calls)

    def test_git_checkout_failure_returns_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Git checkout failure returns Git error skip."""

        def execute_side_effect(cmd: list[str], options: Any) -> Any:
            if "checkout" in cmd:
                raise CalledProcessError(1, cmd, "", "error")
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            execute_side_effect,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.get_folder_git_status",
            lambda folder: "Clean",
        )
        mock_branch_manager = type(
            "MockBranchManager",
            (),
            {
                "get_branch_with_pr_fallback": lambda self, issue_number, repo_owner, repo_name: "feat-branch",
            },
        )()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(False, "Git error", None)

    def test_git_fetch_always_runs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git fetch origin runs for all statuses."""
        execute_calls: list[Any] = []

        def mock_execute(cmd: list[str], options: Any) -> Any:
            execute_calls.append(cmd)
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            mock_execute,
        )
        mock_branch_manager = type("MockBranchManager", (), {})()

        _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=123,
            repo_owner="test-owner",
            repo_name="test-repo",
        )

        # First call should be git fetch
        assert len(execute_calls) >= 1
        assert "fetch" in str(execute_calls[0])

    def test_git_fetch_failure_returns_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Git fetch failure returns Git error skip."""

        def execute_side_effect(cmd: list[str], options: Any) -> Any:
            if "fetch" in cmd:
                raise CalledProcessError(1, cmd, "", "error")
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            execute_side_effect,
        )
        mock_branch_manager = type("MockBranchManager", (), {})()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=123,
            repo_owner="test-owner",
            repo_name="test-repo",
        )

        assert result == BranchPrepResult(False, "Git error", None)

    def test_multi_branch_returns_skip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Multiple branches (returns None) results in No branch skip."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            lambda cmd, options: type(
                "Result", (), {"stdout": "", "stderr": "", "return_code": 0}
            )(),
        )
        mock_branch_manager = type(
            "MockBranchManager",
            (),
            {
                "get_branch_with_pr_fallback": lambda self, issue_number, repo_owner, repo_name: None,
            },
        )()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
            repo_owner="owner",
            repo_name="repo",
        )

        assert result == BranchPrepResult(False, "No branch", None)
