"""Test VSCode launch functions for orchestrator."""

import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.session_launch import (
    launch_vscode,
    process_eligible_issues,
)


class TestLaunch:
    """Test VSCode launch functions."""

    def test_launch_vscode_returns_pid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns PID from launch_process."""

        def mock_launch_process(
            cmd: list[str] | str, cwd: str | Path | None = None, shell: bool = False
        ) -> int:
            return 12345

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_process",
            mock_launch_process,
        )

        workspace = tmp_path / "test.code-workspace"
        workspace.touch()

        pid = launch_vscode(workspace)
        assert pid == 12345

    def test_launch_vscode_uses_code_command(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Calls 'code' with workspace path."""
        captured_args: list[Any] = []
        captured_kwargs: dict[str, Any] = {}

        def mock_launch_process(
            cmd: list[str] | str, cwd: str | Path | None = None, shell: bool = False
        ) -> int:
            captured_args.append(cmd)
            captured_kwargs["shell"] = shell
            return 1

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_process",
            mock_launch_process,
        )

        workspace = tmp_path / "test.code-workspace"
        workspace.touch()

        launch_vscode(workspace)

        # The command can be a list or a string (shell=True on Windows)
        cmd = captured_args[0]
        if isinstance(cmd, str):
            # Windows: shell command string like 'code "path"'
            assert "code" in cmd
            assert str(workspace) in cmd
        else:
            # Linux: list like ['code', 'path']
            assert "code" in cmd
            assert str(workspace) in cmd


class TestProcessEligibleIssuesBranchRequirement:
    """Tests for branch requirement enforcement in process_eligible_issues()."""

    def test_status_01_without_branch_launches_on_main(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-01 without linked branch launches session on main."""
        # Setup mocks
        mock_issue: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/123",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_linked_branches.return_value = []

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_linked_branch_for_issue",
            lambda *args, **kwargs: None,  # No linked branch
        )

        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count",
            lambda: 0,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
        )

        # Session should be launched with branch_name=None (defaults to main)
        mock_launch.assert_called_once()
        call_kwargs = mock_launch.call_args.kwargs
        assert call_kwargs["branch_name"] is None

    def test_status_04_without_branch_skips_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """status-04 without linked branch skips issue and logs error."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Plan Review Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/456",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_linked_branches.return_value = []

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_linked_branch_for_issue",
            lambda *args, **kwargs: None,  # No linked branch
        )

        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count",
            lambda: 0,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
            )

        # Session should NOT be launched
        mock_launch.assert_not_called()
        # Error should be logged
        assert "no linked branch" in caplog.text.lower()
        assert "#456" in caplog.text
        # Empty result
        assert result == []

    def test_status_07_without_branch_skips_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """status-07 without linked branch skips issue."""
        mock_issue: IssueData = {
            "number": 789,
            "title": "Code Review Issue",
            "labels": ["status-07:code-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/789",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_linked_branches.return_value = []

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_linked_branch_for_issue",
            lambda *args, **kwargs: None,
        )

        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count",
            lambda: 0,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
            )

        mock_launch.assert_not_called()
        assert result == []

    def test_status_04_with_branch_launches_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-04 with linked branch launches session normally."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Plan Review Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/456",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_linked_branches.return_value = ["feat-456"]

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_linked_branch_for_issue",
            lambda *args, **kwargs: "feat-456",  # Has linked branch
        )

        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count",
            lambda: 0,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
        )

        mock_launch.assert_called_once()
        call_kwargs = mock_launch.call_args.kwargs
        assert call_kwargs["branch_name"] == "feat-456"

    def test_status_04_with_multiple_branches_skips_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """status-04 with multiple linked branches skips issue and logs error."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Plan Review Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/456",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_linked_branches.return_value = [
            "feat-456-v1",
            "feat-456-v2",
        ]

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )

        # Mock get_linked_branch_for_issue to raise ValueError (multiple branches)
        def mock_get_linked_branch(*args: Any, **kwargs: Any) -> None:
            raise ValueError("Multiple branches linked to issue")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_linked_branch_for_issue",
            mock_get_linked_branch,
        )

        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count",
            lambda: 0,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
            )

        # Session should NOT be launched
        mock_launch.assert_not_called()
        # Error should be logged
        assert "multiple branches" in caplog.text.lower()
        assert "#456" in caplog.text
        # Empty result
        assert result == []


class TestProcessEligibleIssuesPrefetchedIssues:
    """Tests for pre-fetched issues bypassing get_all_cached_issues."""

    def test_pre_fetched_issues_bypasses_get_all_cached_issues(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When all_cached_issues is passed, get_all_cached_issues is not called."""
        mock_issue: IssueData = {
            "number": 101,
            "title": "Pre-fetched Issue",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/101",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_linked_branches.return_value = []

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # get_all_cached_issues must NOT be called — raises AssertionError if invoked
        def _should_not_be_called(*args: Any, **kwargs: Any) -> list[IssueData]:
            raise AssertionError("get_all_cached_issues should not be called")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            _should_not_be_called,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_linked_branch_for_issue",
            lambda *args, **kwargs: None,
        )

        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count",
            lambda: 0,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        # Pass pre-fetched issues directly — get_all_cached_issues must not be called
        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            all_cached_issues=[mock_issue],
        )

        # The pre-fetched issue was used: session was launched once
        mock_launch.assert_called_once()
