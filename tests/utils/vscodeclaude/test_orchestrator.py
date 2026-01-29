"""Test orchestration functions for VSCode Claude."""

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.utils.vscodeclaude.orchestrator import (
    get_stage_display_name,
    handle_pr_created_issues,
    launch_vscode,
    prepare_and_launch_session,
    process_eligible_issues,
    restart_closed_sessions,
    truncate_title,
)
from mcp_coder.utils.vscodeclaude.sessions import load_sessions
from mcp_coder.utils.vscodeclaude.types import (
    STAGE_DISPLAY_NAMES,
    VSCODECLAUDE_PRIORITY,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
)


class TestLaunch:
    """Test VSCode launch functions."""

    def test_launch_vscode_returns_pid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns PID from Popen."""
        mock_process = Mock()
        mock_process.pid = 12345

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.subprocess.Popen",
            lambda *args, **kwargs: mock_process,
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

        def mock_popen(args: Any, **kwargs: Any) -> Mock:
            captured_args.append(args)
            captured_kwargs.update(kwargs)
            return Mock(pid=1)

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.subprocess.Popen",
            mock_popen,
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

    def test_get_stage_display_name_known_statuses(self) -> None:
        """Returns human-readable stage names."""
        assert get_stage_display_name("status-07:code-review") == "CODE REVIEW"
        assert get_stage_display_name("status-04:plan-review") == "PLAN REVIEW"
        assert get_stage_display_name("status-01:created") == "ISSUE ANALYSIS"
        assert get_stage_display_name("status-10:pr-created") == "PR CREATED"

    def test_get_stage_display_name_unknown_status(self) -> None:
        """Returns uppercased status for unknown statuses."""
        result = get_stage_display_name("unknown-status")
        assert result == "UNKNOWN-STATUS"

    def test_truncate_title_short(self) -> None:
        """Returns unchanged if under max length."""
        assert truncate_title("Short title", 50) == "Short title"

    def test_truncate_title_exact_length(self) -> None:
        """Returns unchanged if exactly at max length."""
        title = "A" * 50
        result = truncate_title(title, 50)
        assert result == title
        assert len(result) == 50

    def test_truncate_title_long(self) -> None:
        """Truncates with ellipsis if over max."""
        long_title = "A" * 100
        result = truncate_title(long_title, 50)
        assert len(result) == 50
        assert result.endswith("...")
        # Should have 47 'A's followed by '...'
        assert result == "A" * 47 + "..."

    def test_stage_display_names_coverage(self) -> None:
        """All priority statuses have display names."""
        for status in VSCODECLAUDE_PRIORITY:
            assert status in STAGE_DISPLAY_NAMES


class TestOrchestration:
    """Test main orchestration functions."""

    def test_prepare_and_launch_session_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates session with all components."""
        # Mock all dependencies
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.create_working_folder",
            lambda p: True,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.setup_git_repo",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.validate_mcp_json",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.update_gitignore",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.create_workspace_file",
            lambda *args, **kwargs: tmp_path / "test.code-workspace",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.create_startup_script",
            lambda *args, **kwargs: tmp_path / ".vscodeclaude_start.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.create_vscode_task",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.create_status_file",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.launch_vscode",
            lambda p: 9999,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.add_session",
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
            "mcp_coder.utils.vscodeclaude.orchestrator.create_working_folder",
            mock_create_folder,
        )

        def failing_git(*args: Any, **kwargs: Any) -> None:
            raise subprocess.CalledProcessError(1, "git clone")

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.setup_git_repo",
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

        with pytest.raises(subprocess.CalledProcessError):
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
            "mcp_coder.utils.vscodeclaude.orchestrator.create_working_folder",
            mock_create_folder,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.setup_git_repo",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.validate_mcp_json",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.validate_setup_commands",
            lambda c: None,
        )

        def failing_setup(*args: Any, **kwargs: Any) -> None:
            raise subprocess.CalledProcessError(1, "uv sync")

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.run_setup_commands",
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
            "mcp_coder.utils.vscodeclaude.orchestrator.platform.system",
            lambda: "Windows",
        )

        with pytest.raises(subprocess.CalledProcessError):
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
            "mcp_coder.utils.vscodeclaude.orchestrator.get_active_session_count",
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
            "mcp_coder.utils.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode not running
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.check_vscode_running",
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

    def test_restart_closed_sessions_relaunches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relaunches VSCode for valid sessions."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode not running - patch at orchestrator since that's where it's imported
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False,
        )

        # Mock is_session_stale to avoid GitHub API calls - patch at orchestrator
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.is_session_stale",
            lambda session: False,
        )

        # Create working folder and workspace file
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_123.code-workspace"
        workspace_file.write_text("{}")

        # Mock launch_vscode
        new_pid = 9999
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.launch_vscode",
            lambda w: new_pid,
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

        restarted = restart_closed_sessions()

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
            "mcp_coder.utils.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode running
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.check_vscode_running",
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
