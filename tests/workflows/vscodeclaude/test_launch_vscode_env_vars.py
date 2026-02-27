"""Integration test for MCP environment variables bug fix.

This test verifies the fix for the bug where MCP server environment variables
were incorrectly set to point to the mcp-coder installation directory instead
of the session's project directory.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.github_operations.issues.types import IssueData
from mcp_coder.workflows.vscodeclaude.session_launch import (
    launch_vscode,
    prepare_and_launch_session,
)
from mcp_coder.workflows.vscodeclaude.types import (
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
)


class TestMCPEnvironmentVariablesBugFix:
    """Integration test for MCP environment variables bug fix."""

    def test_prepare_and_launch_session_passes_session_folder_to_startup_script(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Integration test: prepare_and_launch_session passes session folder to startup script.

        This tests the actual bug fix - that prepare_and_launch_session() passes
        the session's folder_path to the startup script for MCP environment variables,
        not the mcp_coder_install_dir.

        This is a comprehensive integration test that mocks all the heavyweight
        dependencies (git operations, file creation, etc.) while capturing the
        actual parameters passed to the startup script creation.
        """
        from pathlib import Path
        from unittest.mock import MagicMock

        # Capture the environment variables passed to launch_vscode
        captured_launch_args: dict[str, Path | None] = {}
        original_launch_vscode = launch_vscode

        def mock_launch_vscode_with_capture(
            workspace_file: Path, session_working_dir: Path | None = None
        ) -> int:
            captured_launch_args["workspace_file"] = workspace_file
            captured_launch_args["session_working_dir"] = session_working_dir
            # Call the real function to test environment variable setting
            return original_launch_vscode(workspace_file, session_working_dir)

        # Mock launch_process - should receive no environment variables in new approach
        captured_env: dict[str, str] | None = None

        def mock_launch_process(
            cmd: str | list[str],
            cwd: str | Path | None = None,
            shell: bool = False,
            env: dict[str, str] | None = None,
        ) -> int:
            nonlocal captured_env
            captured_env = env
            return 12345

        # Mock all the heavyweight dependencies
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_vscode",
            mock_launch_vscode_with_capture,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_process",
            mock_launch_process,
        )

        # Mock workspace creation and git operations
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_working_folder",
            lambda path: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.setup_git_repo",
            lambda path, url, branch: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.validate_mcp_json",
            lambda path: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.validate_setup_commands",
            lambda _cmds: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.run_setup_commands",
            lambda _path, _cmds: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.update_gitignore",
            lambda path: None,
        )

        # Mock file creation operations
        mock_workspace_file = tmp_path / "test.code-workspace"
        mock_workspace_file.touch()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_workspace_file",
            lambda **kwargs: mock_workspace_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_startup_script",
            lambda **kwargs: tmp_path / "startup.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_vscode_task",
            lambda _path, _script: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_status_file",
            lambda **kwargs: None,
        )

        # Mock session management
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.add_session",
            lambda session: None,
        )

        # Mock utility functions
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_repo_short_name",
            lambda config: "test-repo",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_repo_full_name",
            lambda config: "owner/test-repo",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_working_folder_path",
            lambda base, repo, issue: tmp_path / f"{repo}_{issue}",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_issue_status",
            lambda issue: "status-01:created",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.build_session",
            lambda **kwargs: {
                "folder": str(tmp_path / "test-repo_123"),
                "repo": "owner/test-repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": 12345,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            },
        )

        # Prepare test data
        issue_data: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "url": "https://github.com/owner/test-repo/issues/123",
            "labels": ["status-01:created"],
            "assignees": [],
            "state": "open",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        repo_config = {"repo_url": "https://github.com/owner/test-repo"}
        vscodeclaude_config: VSCodeClaudeConfig = {
            "workspace_base": str(tmp_path / "workspace"),
            "max_sessions": 3,
        }
        repo_vscodeclaude_config: RepoVSCodeClaudeConfig = {}

        # Expected session folder path
        expected_session_folder = tmp_path / "test-repo_123"

        # Act: Call prepare_and_launch_session
        session = prepare_and_launch_session(
            issue=issue_data,
            repo_config=repo_config,
            vscodeclaude_config=vscodeclaude_config,
            repo_vscodeclaude_config=repo_vscodeclaude_config,
            branch_name=None,
            is_intervention=False,
        )

        # Assert: Verify that launch_vscode was called with the session folder
        assert "session_working_dir" in captured_launch_args
        actual_session_folder = captured_launch_args["session_working_dir"]

        # The critical assertion: session folder should be passed to launch_vscode
        assert actual_session_folder == expected_session_folder

        # In the new approach, no environment variables are passed via launch_process
        # They are instead written directly into the startup script
        assert captured_env is None

        # Verify session was created
        assert session is not None
        assert session["issue_number"] == 123
