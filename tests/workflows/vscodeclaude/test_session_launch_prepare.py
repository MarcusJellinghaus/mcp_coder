from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.subprocess_runner import CalledProcessError
from mcp_coder.workflows.vscodeclaude.session_launch import prepare_and_launch_session
from mcp_coder.workflows.vscodeclaude.types import (
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
)
from tests.github_factories import make_issue_data


class TestPrepareAndLaunchSession:
    """Tests for prepare_and_launch_session() success and failure cleanup."""

    def test_prepare_and_launch_session_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates session with all components."""
        # Mock all dependencies
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_working_folder",
            lambda p: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.setup_git_repo",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.validate_mcp_json",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.update_gitignore",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_workspace_file",
            lambda *args, **kwargs: tmp_path / "test.code-workspace",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_startup_script",
            lambda *args, **kwargs: tmp_path / ".vscodeclaude_start.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_vscode_task",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_status_file",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_vscode",
            lambda *args: 9999,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.add_session",
            lambda s: None,
        )

        issue = make_issue_data(
            number=123,
            title="Test issue",
            labels=["status-07:code-review"],
            assignees=["testuser"],
        )

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
            "mcp_coder.workflows.vscodeclaude.session_launch.create_working_folder",
            mock_create_folder,
        )

        def failing_git(*args: Any, **kwargs: Any) -> None:
            raise CalledProcessError(1, "git clone")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.setup_git_repo",
            failing_git,
        )

        issue = make_issue_data(
            number=123,
            title="Test",
            labels=["status-07:code-review"],
            url="...",
        )
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
            "mcp_coder.workflows.vscodeclaude.session_launch.create_working_folder",
            mock_create_folder,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.setup_git_repo",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.validate_mcp_json",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.validate_setup_commands",
            lambda c: None,
        )

        def failing_setup(*args: Any, **kwargs: Any) -> None:
            raise CalledProcessError(1, "uv sync")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.run_setup_commands",
            failing_setup,
        )

        issue = make_issue_data(
            number=123,
            title="Test",
            labels=["status-07:code-review"],
            url="...",
        )
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
            "mcp_coder.workflows.vscodeclaude.session_launch.platform.system",
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
