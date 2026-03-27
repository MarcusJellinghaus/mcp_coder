"""Test VSCode launch functions for orchestrator."""

import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.session_launch import (
    launch_vscode,
    prepare_and_launch_session,
    process_eligible_issues,
    regenerate_session_files,
)
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession


class TestLaunch:
    """Test VSCode launch functions."""

    def test_launch_vscode_returns_pid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns PID from launch_process."""

        def mock_launch_process(
            cmd: list[str] | str,
            cwd: str | Path | None = None,
            shell: bool = False,
            env: dict[str, str] | None = None,
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
            cmd: list[str] | str,
            cwd: str | Path | None = None,
            shell: bool = False,
            env: dict[str, str] | None = None,
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

    def test_launch_vscode_no_longer_sets_environment_variables(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables are no longer passed via process inheritance (fixed approach)."""
        captured_env: dict[str, str] | None = None

        def mock_launch_process(
            cmd: list[str] | str,
            cwd: str | Path | None = None,
            shell: bool = False,
            env: dict[str, str] | None = None,
        ) -> int:
            nonlocal captured_env
            captured_env = env
            return 12345

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_process",
            mock_launch_process,
        )

        workspace = tmp_path / "test.code-workspace"
        workspace.touch()
        mcp_coder_dir = tmp_path / "mcp-coder-install"
        mcp_coder_dir.mkdir()

        launch_vscode(workspace, mcp_coder_dir)

        # After the fix: no environment variables are passed via launch_process
        # They are now set directly in the startup script
        assert captured_env is None

    def test_launch_vscode_no_env_variables_passed_to_process(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No environment variables are passed to launch_process (fixed approach)."""
        captured_env: dict[str, str] | None = None

        def mock_launch_process(
            cmd: list[str] | str,
            cwd: str | Path | None = None,
            shell: bool = False,
            env: dict[str, str] | None = None,
        ) -> int:
            nonlocal captured_env
            captured_env = env
            return 12345

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_process",
            mock_launch_process,
        )

        workspace = tmp_path / "test.code-workspace"
        workspace.touch()
        mcp_coder_dir = tmp_path / "mcp-coder-install"
        mcp_coder_dir.mkdir()

        launch_vscode(workspace, mcp_coder_dir)

        # After the fix: no environment variables are passed via launch_process
        # They are now set directly in the startup script
        assert captured_env is None

    def test_launch_vscode_no_env_when_mcp_dir_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Does not set environment variables when mcp_coder_project_dir is None."""
        captured_env: dict[str, str] | None = None

        def mock_launch_process(
            cmd: list[str] | str,
            cwd: str | Path | None = None,
            shell: bool = False,
            env: dict[str, str] | None = None,
        ) -> int:
            nonlocal captured_env
            captured_env = env
            return 12345

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_process",
            mock_launch_process,
        )

        workspace = tmp_path / "test.code-workspace"
        workspace.touch()

        launch_vscode(workspace, None)

        # Verify no environment variables were set
        assert captured_env is None


class TestFromGithubThreading:
    """Tests for from_github parameter threading through session launch functions."""

    def test_prepare_and_launch_session_passes_from_github_to_startup_script(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """prepare_and_launch_session passes from_github=True to create_startup_script."""
        from unittest.mock import patch

        folder_path = tmp_path / "repo_42"
        folder_path.mkdir()

        mock_issue: IssueData = {
            "number": 42,
            "title": "Test",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/42",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock all workspace functions
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_working_folder_path",
            lambda *a, **kw: folder_path,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_working_folder",
            lambda *a, **kw: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.setup_git_repo",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.validate_mcp_json",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.update_gitignore",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_workspace_file",
            lambda *a, **kw: tmp_path / "test.code-workspace",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_vscode_task",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_status_file",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_vscode",
            lambda *a, **kw: 9999,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.add_session",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_repo_short_name",
            lambda *a, **kw: "repo",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_repo_full_name",
            lambda *a, **kw: "owner/repo",
        )

        mock_create_startup = MagicMock(return_value=tmp_path / "script.bat")
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_startup_script",
            mock_create_startup,
        )

        prepare_and_launch_session(
            issue=mock_issue,
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": str(tmp_path), "max_sessions": 3},
            repo_vscodeclaude_config={},
            branch_name=None,
            from_github=True,
        )

        mock_create_startup.assert_called_once()
        assert mock_create_startup.call_args.kwargs["from_github"] is True

    def test_prepare_and_launch_session_stores_from_github_in_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """prepare_and_launch_session stores from_github=True in session dict."""
        folder_path = tmp_path / "repo_42"
        folder_path.mkdir()

        mock_issue: IssueData = {
            "number": 42,
            "title": "Test",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/42",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_working_folder_path",
            lambda *a, **kw: folder_path,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_working_folder",
            lambda *a, **kw: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.setup_git_repo",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.validate_mcp_json",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.update_gitignore",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_workspace_file",
            lambda *a, **kw: tmp_path / "test.code-workspace",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_startup_script",
            lambda *a, **kw: tmp_path / "script.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_vscode_task",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_status_file",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_vscode",
            lambda *a, **kw: 9999,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.add_session",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_repo_short_name",
            lambda *a, **kw: "repo",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_repo_full_name",
            lambda *a, **kw: "owner/repo",
        )

        session = prepare_and_launch_session(
            issue=mock_issue,
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": str(tmp_path), "max_sessions": 3},
            repo_vscodeclaude_config={},
            branch_name=None,
            from_github=True,
        )

        assert session["from_github"] is True

    def test_process_eligible_issues_passes_from_github(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """process_eligible_issues passes from_github=True to prepare_and_launch_session."""
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

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None

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

        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            from_github=True,
        )

        mock_launch.assert_called_once()
        assert mock_launch.call_args.kwargs["from_github"] is True

    def test_regenerate_session_files_reads_from_github_from_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """regenerate_session_files reads from_github=True from session and passes to create_startup_script."""
        folder_path = tmp_path / "repo_42"
        folder_path.mkdir()
        (folder_path / ".git").mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder_path),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-01:created",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
            "from_github": True,
        }

        issue: IssueData = {
            "number": 42,
            "title": "Test",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/42",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock git branch detection
        from unittest.mock import Mock

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.execute_subprocess",
            lambda *a, **kw: Mock(stdout="main\n"),
        )

        mock_create_startup = MagicMock(return_value=tmp_path / "script.bat")
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_startup_script",
            mock_create_startup,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_vscode_task",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_status_file",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_workspace_file",
            lambda *a, **kw: tmp_path / "test.code-workspace",
        )

        regenerate_session_files(session, issue)

        mock_create_startup.assert_called_once()
        assert mock_create_startup.call_args.kwargs["from_github"] is True

    def test_regenerate_session_files_with_from_github_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """regenerate_session_files passes from_github=False when session has it False."""
        folder_path = tmp_path / "repo_42"
        folder_path.mkdir()
        (folder_path / ".git").mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder_path),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-01:created",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
            "from_github": False,
        }

        issue: IssueData = {
            "number": 42,
            "title": "Test",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/42",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        from unittest.mock import Mock

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.execute_subprocess",
            lambda *a, **kw: Mock(stdout="main\n"),
        )

        mock_create_startup = MagicMock(return_value=tmp_path / "script.bat")
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_startup_script",
            mock_create_startup,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_vscode_task",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_status_file",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_workspace_file",
            lambda *a, **kw: tmp_path / "test.code-workspace",
        )

        regenerate_session_files(session, issue)

        mock_create_startup.assert_called_once()
        assert mock_create_startup.call_args.kwargs["from_github"] is False


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
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None

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
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None

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
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None

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
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "feat-456"

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
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None

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
