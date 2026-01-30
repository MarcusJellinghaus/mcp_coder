"""Test regenerate_session_files creates all required files."""

import json
import platform
from pathlib import Path
from unittest.mock import Mock

import pytest

from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.utils.vscodeclaude.orchestrator import regenerate_session_files
from mcp_coder.utils.vscodeclaude.types import VSCodeClaudeSession


@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Windows-only test: Linux V2 templates not yet implemented",
)
class TestRegenerateSessionFiles:
    """Test regenerate_session_files creates all required files."""

    @pytest.fixture
    def session_folder(self, tmp_path: Path) -> Path:
        """Create a mock session folder with git repo."""
        folder = tmp_path / "repo_123"
        folder.mkdir()
        # Create minimal .git dir to simulate git repo
        git_dir = folder / ".git"
        git_dir.mkdir()
        return folder

    @pytest.fixture
    def mock_issue(self) -> IssueData:
        """Create a mock issue."""
        return {
            "number": 123,
            "title": "Test issue for regeneration",
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

    @pytest.fixture
    def mock_session(self, session_folder: Path) -> VSCodeClaudeSession:
        """Create a mock session."""
        return {
            "folder": str(session_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }

    def test_regenerate_creates_startup_script(
        self,
        session_folder: Path,
        mock_session: VSCodeClaudeSession,
        mock_issue: IssueData,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regenerate creates startup script (.bat or .sh)."""
        # Mock git branch detection
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: Mock(returncode=0, stdout="main\n"),
        )

        script_path = regenerate_session_files(mock_session, mock_issue)

        assert script_path.exists()
        assert script_path.name.startswith(".vscodeclaude_start")

    def test_regenerate_creates_tasks_json(
        self,
        session_folder: Path,
        mock_session: VSCodeClaudeSession,
        mock_issue: IssueData,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regenerate creates .vscode/tasks.json for auto-run on folder open."""
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: Mock(returncode=0, stdout="main\n"),
        )

        regenerate_session_files(mock_session, mock_issue)

        tasks_file = session_folder / ".vscode" / "tasks.json"
        assert tasks_file.exists(), "tasks.json must be created for auto-run"

        content = json.loads(tasks_file.read_text())
        assert "tasks" in content
        assert len(content["tasks"]) > 0
        assert content["tasks"][0]["runOptions"]["runOn"] == "folderOpen"

    def test_regenerate_creates_status_file(
        self,
        session_folder: Path,
        mock_session: VSCodeClaudeSession,
        mock_issue: IssueData,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regenerate creates .vscodeclaude_status.md."""
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: Mock(returncode=0, stdout="main\n"),
        )

        regenerate_session_files(mock_session, mock_issue)

        status_file = session_folder / ".vscodeclaude_status.md"
        assert status_file.exists()
        content = status_file.read_text(encoding="utf-8")
        assert "#123" in content
        assert "Test issue for regeneration" in content

    def test_regenerate_creates_workspace_file(
        self,
        tmp_path: Path,
        session_folder: Path,
        mock_session: VSCodeClaudeSession,
        mock_issue: IssueData,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regenerate creates .code-workspace file."""
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: Mock(returncode=0, stdout="main\n"),
        )

        regenerate_session_files(mock_session, mock_issue)

        workspace_file = tmp_path / "repo_123.code-workspace"
        assert workspace_file.exists()

        content = json.loads(workspace_file.read_text())
        assert "folders" in content
        assert "settings" in content

    def test_regenerate_workspace_has_auto_task_setting(
        self,
        tmp_path: Path,
        session_folder: Path,
        mock_session: VSCodeClaudeSession,
        mock_issue: IssueData,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Workspace file must have task.allowAutomaticTasks setting."""
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: Mock(returncode=0, stdout="main\n"),
        )

        regenerate_session_files(mock_session, mock_issue)

        workspace_file = tmp_path / "repo_123.code-workspace"
        content = json.loads(workspace_file.read_text())

        assert "task.allowAutomaticTasks" in content["settings"]
        assert content["settings"]["task.allowAutomaticTasks"] == "on"

    def test_regenerate_creates_all_files(
        self,
        tmp_path: Path,
        session_folder: Path,
        mock_session: VSCodeClaudeSession,
        mock_issue: IssueData,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regenerate must create ALL required files for session restart.

        This is a comprehensive test to prevent regression where files
        are forgotten during regeneration.
        """
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: Mock(returncode=0, stdout="main\n"),
        )

        regenerate_session_files(mock_session, mock_issue)

        # All required files must exist
        required_files = [
            session_folder / ".vscodeclaude_status.md",
            session_folder / ".vscode" / "tasks.json",
            tmp_path / "repo_123.code-workspace",
        ]

        # Startup script (platform-specific)
        startup_bat = session_folder / ".vscodeclaude_start.bat"
        startup_sh = session_folder / ".vscodeclaude_start.sh"
        assert startup_bat.exists() or startup_sh.exists(), "Startup script missing"

        for file_path in required_files:
            assert file_path.exists(), f"Required file missing: {file_path}"
