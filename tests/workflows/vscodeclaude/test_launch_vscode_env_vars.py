"""Test launch_vscode environment variables bug.

This test demonstrates and verifies the fix for the bug where MCP server
environment variables were incorrectly set to point to the mcp-coder
installation directory instead of the session's project directory.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflows.vscodeclaude.session_launch import (
    launch_vscode,
    prepare_and_launch_session,
)


class TestLaunchVSCodeEnvironmentVariables:
    """Test environment variable handling in launch_vscode function."""

    def test_mcp_env_vars_point_to_session_folder_not_mcp_coder_install(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP environment variables should point to session folder, not mcp-coder install.

        This test demonstrates the bug where MCP_CODER_PROJECT_DIR and MCP_CODER_VENV_DIR
        were incorrectly set to the mcp-coder installation directory instead of the
        session's working directory.

        The bug is in prepare_and_launch_session() which passes mcp_coder_install_dir
        to launch_vscode() instead of the session's folder_path.

        Expected behavior:
        - MCP_CODER_PROJECT_DIR should be the session folder (e.g., /workspace/mcp-code-checker_82)
        - MCP_CODER_VENV_DIR should be session_folder/.venv

        Bug behavior (before fix):
        - MCP_CODER_PROJECT_DIR was set to mcp-coder installation dir
        - MCP_CODER_VENV_DIR was set to mcp-coder-install/.venv
        """
        # Capture environment variables passed to launch_process
        captured_env: dict[str, str] = {}

        def mock_launch_process(
            cmd: str | list[str],
            cwd: str | Path | None = None,
            shell: bool = False,
            env: dict[str, str] | None = None,
        ) -> int:
            if env:
                captured_env.update(env)
            return 12345

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_process",
            mock_launch_process,
        )

        # Set up test paths
        workspace_file = tmp_path / "test.code-workspace"
        workspace_file.touch()

        # This represents the session's working directory (e.g., /workspace/mcp-code-checker_82)
        session_folder = tmp_path / "session_working_dir"
        session_folder.mkdir()

        # This represents where mcp-coder is installed (different from session folder)
        mcp_coder_install_dir = tmp_path / "mcp-coder-installation"
        mcp_coder_install_dir.mkdir()

        # TEST THE FIX: launch_vscode should now use session_folder_path parameter
        # This tests the fixed behavior where we pass the session folder
        launch_vscode(workspace_file, session_folder)

        # Verify environment variables point to session folder, not mcp-coder install
        assert "MCP_CODER_PROJECT_DIR" in captured_env
        assert "MCP_CODER_VENV_DIR" in captured_env

        # AFTER THE FIX: These should point to the SESSION folder
        expected_project_dir = str(session_folder)
        expected_venv_dir = str(session_folder / ".venv")

        # These should now pass with the fixed code
        assert captured_env["MCP_CODER_PROJECT_DIR"] == expected_project_dir
        assert captured_env["MCP_CODER_VENV_DIR"] == expected_venv_dir

        # Ensure they do NOT point to mcp-coder installation directory
        assert captured_env["MCP_CODER_PROJECT_DIR"] != str(mcp_coder_install_dir)
        assert captured_env["MCP_CODER_VENV_DIR"] != str(
            mcp_coder_install_dir / ".venv"
        )

    def test_no_env_vars_when_session_folder_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No environment variables should be set when session folder is None."""
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

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.launch_process",
            mock_launch_process,
        )

        workspace_file = tmp_path / "test.code-workspace"
        workspace_file.touch()

        launch_vscode(workspace_file, None)

        # No environment should be set when session folder is None
        assert captured_env is None

    def test_env_vars_preserve_existing_environment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables should preserve existing env vars when setting MCP vars."""
        captured_env: dict[str, str] = {}
        original_env = os.environ.copy()

        # Set a test environment variable that should be preserved
        os.environ["EXISTING_VAR"] = "should_be_preserved"

        def mock_launch_process(
            cmd: str | list[str],
            cwd: str | Path | None = None,
            shell: bool = False,
            env: dict[str, str] | None = None,
        ) -> int:
            if env:
                captured_env.update(env)
            return 12345

        try:
            monkeypatch.setattr(
                "mcp_coder.workflows.vscodeclaude.session_launch.launch_process",
                mock_launch_process,
            )

            workspace_file = tmp_path / "test.code-workspace"
            workspace_file.touch()
            session_folder = tmp_path / "session_dir"
            session_folder.mkdir()

            launch_vscode(workspace_file, session_folder)

            # Existing environment variables should be preserved
            assert "EXISTING_VAR" in captured_env
            assert captured_env["EXISTING_VAR"] == "should_be_preserved"

            # New MCP variables should be added
            assert "MCP_CODER_PROJECT_DIR" in captured_env
            assert captured_env["MCP_CODER_PROJECT_DIR"] == str(session_folder)
            assert "MCP_CODER_VENV_DIR" in captured_env
            assert captured_env["MCP_CODER_VENV_DIR"] == str(session_folder / ".venv")

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    def test_prepare_and_launch_session_sets_correct_env_vars_integration(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Integration test: prepare_and_launch_session passes session folder to launch_vscode.

        This tests the actual bug fix - that prepare_and_launch_session() passes
        the session's folder_path to launch_vscode(), not mcp_coder_install_dir.

        This is a comprehensive integration test that mocks all the heavyweight
        dependencies (git operations, file creation, etc.) while capturing the
        actual environment variables passed to launch_vscode().
        """
        from pathlib import Path
        from unittest.mock import MagicMock

        # Capture the environment variables passed to launch_vscode
        captured_launch_args: dict[str, any] = {}
        original_launch_vscode = launch_vscode

        def mock_launch_vscode_with_capture(
            workspace_file: Path, session_folder_path: Path | None = None
        ) -> int:
            captured_launch_args["workspace_file"] = workspace_file
            captured_launch_args["session_folder_path"] = session_folder_path
            # Call the real function to test environment variable setting
            return original_launch_vscode(workspace_file, session_folder_path)

        # Mock launch_process to capture the actual environment variables
        captured_env: dict[str, str] = {}

        def mock_launch_process(
            cmd: str | list[str],
            cwd: str | Path | None = None,
            shell: bool = False,
            env: dict[str, str] | None = None,
        ) -> int:
            if env:
                captured_env.update(env)
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
            lambda cmds: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.run_setup_commands",
            lambda path, cmds: None,
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
            lambda path, script: None,
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
        issue_data = {
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
        vscodeclaude_config = {"workspace_base": str(tmp_path / "workspace")}
        repo_vscodeclaude_config = {}

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
        assert "session_folder_path" in captured_launch_args
        actual_session_folder = captured_launch_args["session_folder_path"]

        # The critical assertion: session folder should be passed to launch_vscode
        assert actual_session_folder == expected_session_folder

        # Verify the environment variables were set correctly
        assert "MCP_CODER_PROJECT_DIR" in captured_env
        assert "MCP_CODER_VENV_DIR" in captured_env

        # These should point to the session folder, not mcp-coder installation
        assert captured_env["MCP_CODER_PROJECT_DIR"] == str(expected_session_folder)
        assert captured_env["MCP_CODER_VENV_DIR"] == str(
            expected_session_folder / ".venv"
        )

        # Verify session was created
        assert session is not None
        assert session["issue_number"] == 123
