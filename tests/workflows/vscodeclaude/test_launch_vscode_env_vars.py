"""Test launch_vscode environment variables bug.

This test demonstrates and verifies the fix for the bug where MCP server
environment variables were incorrectly set to point to the mcp-coder
installation directory instead of the session's project directory.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflows.vscodeclaude.session_launch import launch_vscode


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
        assert captured_env["MCP_CODER_VENV_DIR"] != str(mcp_coder_install_dir / ".venv")

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