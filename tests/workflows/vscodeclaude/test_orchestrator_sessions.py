"""Test main orchestration functions for VSCode Claude."""

import json
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.utils.subprocess_runner import CalledProcessError
from mcp_coder.workflows.vscodeclaude.orchestrator import (
    BranchPrepResult,
    _prepare_restart_branch,
    handle_pr_created_issues,
    prepare_and_launch_session,
    process_eligible_issues,
    restart_closed_sessions,
)
from mcp_coder.workflows.vscodeclaude.sessions import load_sessions
from mcp_coder.workflows.vscodeclaude.types import (
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
)


class TestOrchestration:
    """Test main orchestration functions."""

    def test_prepare_and_launch_session_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates session with all components."""
        # Mock all dependencies
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_working_folder",
            lambda p: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.setup_git_repo",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.validate_mcp_json",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.update_gitignore",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_workspace_file",
            lambda *args, **kwargs: tmp_path / "test.code-workspace",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_startup_script",
            lambda *args, **kwargs: tmp_path / ".vscodeclaude_start.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_vscode_task",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_status_file",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            lambda p: 9999,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.add_session",
            lambda s: None,
        )

        issue: IssueData = {
            "number": 123,
            "title": "Test issue",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": ["testuser"],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/123",
            "locked": False,
        }

        repo_config = {
            "repo_url": "https://github.com/owner/repo.git",
        }

        vscodeclaude_config: VSCodeClaudeConfig = {
            "workspace_base": str(tmp_path),
            "max_sessions": 3,
        }

        session = prepare_and_launch_session(
            issue=issue,
            repo_config=repo_config,
            vscodeclaude_config=vscodeclaude_config,
            repo_vscodeclaude_config={},
            branch_name="main",
            is_intervention=False,
        )

        assert session["issue_number"] == 123
        assert session["vscode_pid"] == 9999
        assert session["is_intervention"] is False
        assert session["repo"] == "owner/repo"
        assert session["status"] == "status-07:code-review"

    def test_prepare_and_launch_aborts_on_git_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Aborts session and cleans up folder if git fails."""

        # Create the folder that will be cleaned up
        folder_path = tmp_path / "repo_123"

        def mock_create_folder(p: Path) -> bool:
            p.mkdir(parents=True, exist_ok=True)
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_working_folder",
            mock_create_folder,
        )

        def failing_git(*args: Any, **kwargs: Any) -> None:
            raise CalledProcessError(1, "git clone")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.setup_git_repo",
            failing_git,
        )

        issue: IssueData = {
            "number": 123,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "...",
            "locked": False,
        }
        repo_config = {"repo_url": "https://github.com/owner/repo.git"}
        vscodeclaude_config: VSCodeClaudeConfig = {
            "workspace_base": str(tmp_path),
            "max_sessions": 3,
        }

        with pytest.raises(CalledProcessError):
            prepare_and_launch_session(
                issue=issue,
                repo_config=repo_config,
                vscodeclaude_config=vscodeclaude_config,
                repo_vscodeclaude_config={},
                branch_name="main",
                is_intervention=False,
            )

        # Folder should be cleaned up on failure
        assert not folder_path.exists()

    def test_prepare_and_launch_aborts_on_setup_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Aborts session and cleans up folder if setup commands fail."""

        folder_path = tmp_path / "repo_123"

        def mock_create_folder(p: Path) -> bool:
            p.mkdir(parents=True, exist_ok=True)
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_working_folder",
            mock_create_folder,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.setup_git_repo",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.validate_mcp_json",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.validate_setup_commands",
            lambda c: None,
        )

        def failing_setup(*args: Any, **kwargs: Any) -> None:
            raise CalledProcessError(1, "uv sync")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.run_setup_commands",
            failing_setup,
        )

        issue: IssueData = {
            "number": 123,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "...",
            "locked": False,
        }
        repo_config = {"repo_url": "https://github.com/owner/repo.git"}
        vscodeclaude_config: VSCodeClaudeConfig = {
            "workspace_base": str(tmp_path),
            "max_sessions": 3,
        }
        repo_vscodeclaude_config: RepoVSCodeClaudeConfig = {
            "setup_commands_windows": ["uv sync"],
        }

        # Mock platform to Windows to trigger setup commands
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.platform.system",
            lambda: "Windows",
        )

        with pytest.raises(CalledProcessError):
            prepare_and_launch_session(
                issue=issue,
                repo_config=repo_config,
                vscodeclaude_config=vscodeclaude_config,
                repo_vscodeclaude_config=repo_vscodeclaude_config,
                branch_name="main",
                is_intervention=False,
            )

        # Folder should be cleaned up on failure
        assert not folder_path.exists()

    def test_process_eligible_issues_respects_max_sessions(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Doesn't start sessions beyond max."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_active_session_count",
            lambda: 2,
        )

        # Should return empty since already at/above max
        sessions = process_eligible_issues(
            repo_name="test",
            repo_config={"repo_url": "https://github.com/owner/repo.git"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 2},
            max_sessions=2,
        )

        assert sessions == []

    def test_process_eligible_issues_applies_repo_filter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips when repo_filter doesn't match."""
        sessions = process_eligible_issues(
            repo_name="test",
            repo_config={"repo_url": "https://github.com/owner/repo.git"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            repo_filter="other_repo",
        )

        assert sessions == []

    def test_restart_closed_sessions_removes_orphans(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Removes sessions with missing folders."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode not running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )

        # Create session with non-existent folder
        session = {
            "folder": str(tmp_path / "nonexistent"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        restarted = restart_closed_sessions()

        # No sessions restarted
        assert restarted == []

        # Session should be removed
        loaded = load_sessions()
        assert len(loaded["sessions"]) == 0

    def test_restart_closed_sessions_skips_unconfigured_repos(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips sessions for repos not in config file."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode not running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )

        # Mock _get_configured_repos to return a different repo (not owner/unconfigured)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/configured_repo"},  # Different from session's repo
        )

        # Create working folder (so it passes the folder exists check)
        working_folder = tmp_path / "unconfigured_123"
        working_folder.mkdir()

        # Create session for an unconfigured repo
        session = {
            "folder": str(working_folder),
            "repo": "owner/unconfigured",  # Not in configured_repos
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        restarted = restart_closed_sessions()

        # No sessions restarted because repo not in config
        assert restarted == []

        # Session should still exist (not removed, just skipped)
        loaded = load_sessions()
        assert len(loaded["sessions"]) == 1

    def test_restart_closed_sessions_relaunches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relaunches VSCode for valid sessions."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode not running - patch at orchestrator since that's where it's imported
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )

        # Mock _get_configured_repos to return the test repo
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock regenerate_session_files to avoid issue fetching
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )

        # Create working folder and workspace file
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_123.code-workspace"
        workspace_file.write_text("{}")

        # Mock launch_vscode
        new_pid = 9999
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            lambda _: new_pid,
        )

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Provide cached issues to avoid API calls
        cached_issue: IssueData = {
            "number": 123,
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
            "owner/repo": {123: cached_issue}
        }

        restarted = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        assert len(restarted) == 1
        assert restarted[0]["vscode_pid"] == new_pid

        # PID should be updated in store
        loaded = load_sessions()
        assert loaded["sessions"][0]["vscode_pid"] == new_pid

    def test_restart_closed_sessions_skips_running(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips sessions with running VSCode."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: True,
        )

        session = {
            "folder": str(tmp_path / "existing"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        restarted = restart_closed_sessions()

        # No sessions restarted since vscode is running
        assert restarted == []

    def test_handle_pr_created_issues_prints_url(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Prints issue URL for pr-created issues."""

        issue: IssueData = {
            "number": 123,
            "title": "Test issue",
            "body": "",
            "state": "open",
            "labels": ["status-10:pr-created"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/123",
            "locked": False,
        }
        issues: list[IssueData] = [issue]

        handle_pr_created_issues(issues)

        captured = capsys.readouterr()
        assert "#123" in captured.out
        assert "https://github.com/owner/repo/issues/123" in captured.out

    def test_handle_pr_created_issues_empty_list(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Does nothing for empty list."""
        handle_pr_created_issues([])

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_restart_closed_sessions_skips_blocked_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not restart sessions for issues with blocked label."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        # Cached issue with blocked label
        cached_issue: IssueData = {
            "number": 123,
            "title": "Test",
            "state": "open",
            "labels": ["status-01:created", "blocked"],
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

        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        assert len(result) == 0  # Not restarted

    def test_restart_closed_sessions_updates_session_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should update session status when GitHub status differs."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            lambda _: 9999,
        )

        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_123.code-workspace"
        workspace_file.write_text("{}")

        # Track status updates
        status_updates = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.update_session_status",
            lambda folder, status: status_updates.append((folder, status)),
        )

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",  # Old status
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        # GitHub has new status
        cached_issue: IssueData = {
            "number": 123,
            "title": "Test",
            "state": "open",
            "labels": ["status-04:plan-review"],  # Changed status
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

        # Verify status was updated
        assert len(status_updates) == 1
        assert status_updates[0][0] == str(working_folder)
        assert status_updates[0][1] == "status-04:plan-review"

    def test_restart_closed_sessions_skips_closed_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not restart sessions for closed issues."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Create working folder (so it passes folder exists check)
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Cached issue is CLOSED
        cached_issue: IssueData = {
            "number": 123,
            "title": "Test",
            "state": "closed",  # <-- Issue is closed
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
            "owner/repo": {123: cached_issue}
        }

        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Session should NOT be restarted because issue is closed
        assert len(result) == 0

    def test_restart_closed_sessions_skips_bot_stage_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not restart sessions when issue moved to bot stage."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Create working folder
        working_folder = tmp_path / "repo_456"
        working_folder.mkdir()

        # Session was at code-review, but issue has moved to bot stage
        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-07:code-review",  # Old status
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Issue is now at bot stage (status-08:ready-pr) - NOT eligible
        cached_issue: IssueData = {
            "number": 456,
            "title": "Test",
            "state": "open",
            "labels": ["status-08:ready-pr"],  # <-- Bot stage, not eligible
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

        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Session should NOT be restarted - bot stage is not eligible
        assert len(result) == 0

    def test_restart_closed_sessions_skips_pr_created_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not restart sessions when issue moved to pr-created."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Create working folder
        working_folder = tmp_path / "repo_789"
        working_folder.mkdir()

        # Session was at code-review, but issue now has PR created
        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-07:code-review",  # Old status
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Issue is now at pr-created - NOT eligible (no session needed)
        cached_issue: IssueData = {
            "number": 789,
            "title": "Test",
            "state": "open",
            "labels": ["status-10:pr-created"],  # <-- PR created, not eligible
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

        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Session should NOT be restarted - pr-created is not eligible
        assert len(result) == 0

    def test_restart_closed_sessions_restarts_eligible_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should restart sessions for eligible issues (01, 04, 07)."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            lambda _: 9999,
        )

        # Create working folder and workspace file
        working_folder = tmp_path / "repo_101"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_101.code-workspace"
        workspace_file.write_text("{}")

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 101,
            "status": "status-04:plan-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Issue is at eligible status (04), open
        cached_issue: IssueData = {
            "number": 101,
            "title": "Test",
            "state": "open",
            "labels": ["status-04:plan-review"],  # <-- Eligible status
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {101: cached_issue}
        }

        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Session SHOULD be restarted - eligible status, open issue
        assert len(result) == 1
        assert result[0]["vscode_pid"] == 9999

    def test_restart_closed_sessions_eligible_to_eligible_transition(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should restart when status changes between eligible statuses (04 → 07)."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            lambda _: 8888,
        )

        # Track status updates
        status_updates: list[tuple[str, str]] = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.update_session_status",
            lambda folder, status: status_updates.append((folder, status)),
        )

        # Create working folder and workspace file
        working_folder = tmp_path / "repo_202"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_202.code-workspace"
        workspace_file.write_text("{}")

        # Session was at 04 (plan-review)
        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 202,
            "status": "status-04:plan-review",  # Old eligible status
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Issue has moved to 07 (code-review) - ALSO eligible
        cached_issue: IssueData = {
            "number": 202,
            "title": "Test",
            "state": "open",
            "labels": ["status-07:code-review"],  # <-- New eligible status
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {202: cached_issue}
        }

        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Session SHOULD be restarted - both statuses are eligible
        assert len(result) == 1
        assert result[0]["vscode_pid"] == 8888

        # Status should have been updated from 04 to 07
        assert len(status_updates) == 1
        assert status_updates[0][0] == str(working_folder)
        assert status_updates[0][1] == "status-07:code-review"


class TestPrepareRestartBranch:
    """Tests for _prepare_restart_branch() helper."""

    def test_status_01_skips_branch_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-01 doesn't require branch - returns success immediately."""
        # Mock git fetch to succeed
        mock_execute = monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
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
        )

        assert result == BranchPrepResult(True, None, None)

    def test_status_04_no_branch_returns_skip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-04 without linked branch returns No branch skip."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            lambda cmd, options: type(
                "Result", (), {"stdout": "", "stderr": "", "return_code": 0}
            )(),
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            lambda bm, issue_num: None,
        )
        mock_branch_manager = type("MockBranchManager", (), {})()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
        )

        assert result == BranchPrepResult(False, "No branch", None)

    def test_status_07_dirty_returns_skip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-07 with dirty repo returns Dirty skip."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            lambda cmd, options: type(
                "Result", (), {"stdout": "", "stderr": "", "return_code": 0}
            )(),
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            lambda bm, issue_num: "feat-branch",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_folder_git_status",
            lambda folder: "Dirty",
        )
        mock_branch_manager = type("MockBranchManager", (), {})()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-07:code-review",
            branch_manager=mock_branch_manager,
            issue_number=456,
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            lambda bm, issue_num: "feat-123",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_folder_git_status",
            lambda folder: "Clean",
        )
        mock_branch_manager = type("MockBranchManager", (), {})()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            execute_side_effect,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            lambda bm, issue_num: "feat-branch",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_folder_git_status",
            lambda folder: "Clean",
        )
        mock_branch_manager = type("MockBranchManager", (), {})()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            mock_execute,
        )
        mock_branch_manager = type("MockBranchManager", (), {})()

        _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=123,
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            execute_side_effect,
        )
        mock_branch_manager = type("MockBranchManager", (), {})()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=123,
        )

        assert result == BranchPrepResult(False, "Git error", None)

    def test_multi_branch_returns_skip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Multiple branches linked to issue returns Multi-branch skip."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            lambda cmd, options: type(
                "Result", (), {"stdout": "", "stderr": "", "return_code": 0}
            )(),
        )

        def raise_value_error(bm: Any, issue_num: int) -> str:
            raise ValueError("Multiple branches linked")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            raise_value_error,
        )
        mock_branch_manager = type("MockBranchManager", (), {})()

        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
        )

        assert result == BranchPrepResult(False, "Multi-branch", None)


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
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Track calls to _prepare_restart_branch
        prepare_calls: list[dict[str, Any]] = []

        def mock_prepare(
            folder_path: Path,
            current_status: str,
            branch_manager: Any,
            issue_number: int,
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
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
            mock_prepare,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
            lambda **kwargs: BranchPrepResult(True, None, "feat-123"),
        )

        # Track calls to create_status_file across all modules
        status_file_calls: list[dict[str, Any]] = []

        def mock_create_status(**kwargs: Any) -> None:
            status_file_calls.append(kwargs)

        # Patch create_status_file in both orchestrator and workspace modules
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_status_file",
            mock_create_status,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.create_status_file",
            mock_create_status,
        )

        # Mock git rev-parse to return the branch that was checked out
        def mock_execute(cmd: list[str], options: Any) -> Any:
            if "rev-parse" in cmd and "--abbrev-ref" in cmd:
                return type(
                    "Result", (), {"stdout": "feat-123", "stderr": "", "return_code": 0}
                )()
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            mock_execute,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_status_file",
            mock_create_status,
        )
        # Also patch in workspace module since that's where it's imported from
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.create_status_file",
            mock_create_status,
        )

        # Call regenerate_session_files
        from mcp_coder.workflows.vscodeclaude.orchestrator import (
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


class TestBranchHandlingIntegration:
    """Integration tests for branch handling feature."""

    def test_full_session_lifecycle_status_01_to_04(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test full lifecycle: create at 01, restart when changed to 04."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Phase 1: Mock session at status-01 (no branch required)
        # Session was created on main branch
        working_folder = tmp_path / "repo_100"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_100.code-workspace"
        workspace_file.write_text("{}")

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 100,
            "status": "status-01:created",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Phase 2: Issue status changes to status-04 with linked branch
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Track operations in order
        operations: list[str] = []

        def mock_prepare(
            folder_path: Path,
            current_status: str,
            branch_manager: Any,
            issue_number: int,
        ) -> BranchPrepResult:
            operations.append(f"prepare_branch:{current_status}")
            # Simulate successful branch switch for status-04
            return BranchPrepResult(True, None, "feat-100")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
            mock_prepare,
        )

        def mock_regenerate(session: Any, issue: Any) -> Path:
            operations.append("regenerate_files")
            return tmp_path / "script.bat"

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.regenerate_session_files",
            mock_regenerate,
        )

        def mock_create_status(**kwargs: Any) -> None:
            operations.append(f"create_status:branch={kwargs.get('branch_name')}")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_status_file",
            mock_create_status,
        )

        def mock_launch(workspace: Path) -> int:
            operations.append("launch_vscode")
            return 9999

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            mock_launch,
        )

        status_updates: list[str] = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.update_session_status",
            lambda folder, status: status_updates.append(status),
        )

        # Issue now at status-04 with linked branch
        cached_issue: IssueData = {
            "number": 100,
            "title": "Test Issue",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/100",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {100: cached_issue}
        }

        # Actually call restart_closed_sessions to trigger the restart flow
        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Verify full lifecycle
        assert len(result) == 1
        assert result[0]["vscode_pid"] == 9999

        # Verify operations occurred in order
        assert "prepare_branch:status-04:plan-review" in operations
        assert "regenerate_files" in operations
        assert "create_status:branch=feat-100" in operations
        assert "launch_vscode" in operations

        # Verify status was updated
        assert "status-04:plan-review" in status_updates

    def test_status_04_session_without_branch_skips_completely(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: Any
    ) -> None:
        """Status-04 without branch: doesn't create session, shows indicator."""
        import logging

        # Test process_eligible_issues skipping
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_active_session_count",
            lambda: 0,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_github_username",
            lambda: "testuser",
        )

        mock_issue_manager = type("MockIssueManager", (), {})()
        mock_branch_manager = type("MockBranchManager", (), {})()
        mock_branch_manager.get_linked_branches = lambda issue_num: []

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Mock issue at status-04
        mock_issues: list[IssueData] = [
            {
                "number": 200,
                "title": "Test",
                "state": "open",
                "labels": ["status-04:plan-review"],
                "assignees": ["testuser"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "body": "",
                "locked": False,
            }
        ]

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_all_cached_issues",
            lambda **kwargs: mock_issues,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._filter_eligible_vscodeclaude_issues",
            lambda issues, user: issues,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_session_for_issue",
            lambda repo, num: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_repo_vscodeclaude_config",
            lambda name: {},
        )
        # No linked branch
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            lambda bm, num: None,
        )

        with caplog.at_level(logging.ERROR):
            sessions = process_eligible_issues(
                repo_name="test",
                repo_config={"repo_url": "https://github.com/owner/repo.git"},
                vscodeclaude_config={
                    "workspace_base": str(tmp_path),
                    "max_sessions": 3,
                },
                max_sessions=3,
            )

        # No sessions should be started
        assert sessions == []
        # Log should show error about no linked branch
        assert "no linked branch" in caplog.text.lower()

    def test_dirty_repo_blocks_branch_switch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dirty repo prevents branch switch, shows !! Dirty."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock git fetch success, but dirty status
        def mock_execute(cmd: list[str], options: Any) -> Any:
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            lambda bm, num: "feat-branch",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_folder_git_status",
            lambda folder: "Dirty",
        )

        working_folder = tmp_path / "repo_300"
        working_folder.mkdir()

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 300,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue: IssueData = {
            "number": 300,
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
            "owner/repo": {300: cached_issue}
        }

        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Should NOT restart due to dirty repo
        assert len(result) == 0

    def test_git_fetch_runs_on_every_restart(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git fetch origin runs on every restart regardless of status."""
        fetch_calls: list[str] = []

        def mock_execute(cmd: list[str], options: Any) -> Any:
            if "fetch" in cmd:
                fetch_calls.append("fetch")
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            mock_execute,
        )

        mock_branch_manager = type("MockBranchManager", (), {})()

        # Test with status-01
        result_01 = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=100,
        )
        assert "fetch" in fetch_calls

        fetch_calls.clear()

        # Test with status-04
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            lambda bm, num: "feat-branch",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_folder_git_status",
            lambda folder: "Clean",
        )

        result_04 = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=100,
        )
        assert "fetch" in fetch_calls

        fetch_calls.clear()

        # Test with status-07
        result_07 = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-07:code-review",
            branch_manager=mock_branch_manager,
            issue_number=100,
        )
        assert "fetch" in fetch_calls

    def test_intervention_session_requires_branch_for_status_04(
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
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock the necessary components for restart flow
        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Return "No branch" skip reason
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
            lambda **kwargs: BranchPrepResult(False, "No branch", None),
        )

        working_folder = tmp_path / "repo_intervention"
        working_folder.mkdir()

        # Create intervention session at status-04
        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 500,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": True,  # This is an intervention session
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue: IssueData = {
            "number": 500,
            "title": "Intervention Test",
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
            "owner/repo": {500: cached_issue}
        }

        with caplog.at_level(logging.WARNING):
            result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Should skip - intervention flag doesn't bypass branch requirements
        assert len(result) == 0
        assert "No branch" in caplog.text
