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
