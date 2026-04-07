"""Tests for restart closed sessions branch handling."""

import json
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.session_restart import (
    BranchPrepResult,
    _prepare_restart_branch,
    restart_closed_sessions,
)


class TestRestartClosedSessionsBranchHandling:
    """Tests for branch handling in restart_closed_sessions()."""

    def test_restart_calls_prepare_restart_branch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """restart_closed_sessions() calls _prepare_restart_branch."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Track calls to _prepare_restart_branch
        prepare_calls: list[dict[str, Any]] = []

        def mock_prepare(
            folder_path: Path,
            current_status: str,
            branch_manager: Any,
            issue_number: int,
            repo_owner: str,
            repo_name: str,
        ) -> BranchPrepResult:
            prepare_calls.append(
                {
                    "folder": folder_path,
                    "status": current_status,
                    "issue": issue_number,
                }
            )
            return BranchPrepResult(True, None, None)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            mock_prepare,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.launch_vscode",
            lambda _: 9999,
        )

        # Create working folder and workspace file
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_123.code-workspace"
        workspace_file.write_text("{}")

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
            "install_from_github": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue: IssueData = {
            "number": 123,
            "title": "Test",
            "state": "open",
            "labels": ["status-01:created"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {123: cached_issue}
        }

        restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Verify _prepare_restart_branch was called
        assert len(prepare_calls) == 1
        assert prepare_calls[0]["status"] == "status-01:created"
        assert prepare_calls[0]["issue"] == 123

    def test_restart_skips_status_04_without_branch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: Any
    ) -> None:
        """Status-04 without linked branch skips restart."""
        import logging

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            lambda **kwargs: BranchPrepResult(False, "No branch", None),
        )

        working_folder = tmp_path / "repo_456"
        working_folder.mkdir()

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
            "install_from_github": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue: IssueData = {
            "number": 456,
            "title": "Test",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {456: cached_issue}
        }

        with caplog.at_level(logging.WARNING):
            result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # VSCode should NOT be launched
        assert len(result) == 0
        assert "No branch" in caplog.text

    def test_restart_skips_dirty_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: Any
    ) -> None:
        """Dirty repo skips restart with Dirty reason."""
        import logging

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            lambda **kwargs: BranchPrepResult(False, "Dirty", None),
        )

        working_folder = tmp_path / "repo_789"
        working_folder.mkdir()

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
            "install_from_github": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue: IssueData = {
            "number": 789,
            "title": "Test",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {789: cached_issue}
        }

        with caplog.at_level(logging.WARNING):
            result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        assert len(result) == 0
        assert "Dirty" in caplog.text

    def test_restart_switches_branch_on_status_change(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Status change from 01 to 04 switches branch - status file written once."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            lambda **kwargs: BranchPrepResult(True, None, "feat-123"),
        )

        # Track calls to create_status_file across all modules
        status_file_calls: list[dict[str, Any]] = []

        def mock_create_status(**kwargs: Any) -> None:
            status_file_calls.append(kwargs)

        # Patch create_status_file in both orchestrator and workspace modules
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_status_file",
            mock_create_status,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.create_status_file",
            mock_create_status,
        )

        # Mock create_startup_script to avoid Linux NotImplementedError
        mock_script_path = tmp_path / ".vscodeclaude_start.bat"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_startup_script",
            lambda **kwargs: mock_script_path,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.create_startup_script",
            lambda **kwargs: mock_script_path,
        )

        # Mock git rev-parse to return the branch that was checked out
        def mock_execute(cmd: list[str], options: Any) -> Any:
            if "rev-parse" in cmd and "--abbrev-ref" in cmd:
                return type(
                    "Result", (), {"stdout": "feat-123", "stderr": "", "return_code": 0}
                )()
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.execute_subprocess",
            mock_execute,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.launch_vscode",
            lambda _: 9999,
        )

        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_123.code-workspace"
        workspace_file.write_text("{}")

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
            "install_from_github": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        # Issue is now at status-04
        cached_issue: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/123",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {123: cached_issue}
        }

        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Session should be restarted
        assert len(result) == 1

        # Status file should be called ONCE (inside regenerate_session_files)
        assert len(status_file_calls) == 1
        assert status_file_calls[0]["branch_name"] == "feat-123"

    def test_intervention_session_follows_same_rules(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: Any
    ) -> None:
        """Intervention sessions follow same branch rules."""
        import logging

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            lambda **kwargs: BranchPrepResult(False, "No branch", None),
        )

        working_folder = tmp_path / "repo_999"
        working_folder.mkdir()

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 999,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": True,  # Intervention session
            "install_from_github": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue: IssueData = {
            "number": 999,
            "title": "Test",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {999: cached_issue}
        }

        with caplog.at_level(logging.WARNING):
            result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Should skip even for intervention
        assert len(result) == 0

    def test_regenerate_reads_branch_after_checkout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """regenerate_session_files reads current branch from git after checkout."""
        from unittest.mock import MagicMock

        # Create working folder structure
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()

        from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession

        session: VSCodeClaudeSession = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
            "install_from_github": False,
        }

        issue: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/123",
            "body": "",
            "locked": False,
        }

        # Track execute_subprocess calls
        execute_calls: list[list[str]] = []
        status_file_calls: list[dict[str, Any]] = []

        def mock_execute(cmd: list[str], options: Any) -> Any:
            execute_calls.append(cmd)
            # When git rev-parse is called, return the feature branch
            if "git" in str(cmd) and "rev-parse" in str(cmd):
                return type(
                    "Result",
                    (),
                    {"stdout": "feature/test-branch", "stderr": "", "return_code": 0},
                )()
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        def mock_create_status(**kwargs: Any) -> None:
            status_file_calls.append(kwargs)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_status_file",
            mock_create_status,
        )
        # Also patch in workspace module since that's where it's imported from
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.create_status_file",
            mock_create_status,
        )

        # Mock create_startup_script to avoid Linux NotImplementedError
        mock_script_path = tmp_path / ".vscodeclaude_start.bat"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_startup_script",
            lambda **kwargs: mock_script_path,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.create_startup_script",
            lambda **kwargs: mock_script_path,
        )

        # Call regenerate_session_files
        from mcp_coder.workflows.vscodeclaude.session_launch import (
            regenerate_session_files,
        )

        regenerate_session_files(session, issue)

        # Verify git rev-parse was called to get current branch
        assert any(
            "git" in str(call)
            and "rev-parse" in str(call)
            and "--abbrev-ref" in str(call)
            for call in execute_calls
        ), "git rev-parse --abbrev-ref HEAD should be called"

        # Verify create_status_file was called with branch from git
        assert len(status_file_calls) == 1
        assert status_file_calls[0]["branch_name"] == "feature/test-branch"
