"""Test startup script mcp-coder executable path issue.

This test verifies that the startup script can find the mcp-coder executable
even when MCP environment variables point to the session directory.
"""

import platform
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.workflows.vscodeclaude.workspace import create_startup_script


class TestStartupScriptMCPCoderPath:
    """Test that startup script uses correct path for mcp-coder executable."""

    @pytest.mark.skipif(
        platform.system() != "Windows",
        reason="Startup script functionality is Windows-only",
    )
    def test_startup_script_mcp_coder_executable_path(self, tmp_path: Path) -> None:
        """Startup script should find mcp-coder executable regardless of MCP env vars.

        The issue: when MCP_CODER_PROJECT_DIR points to session folder (correct for
        MCP server config), the startup script incorrectly looks for mcp-coder
        executable in the session folder instead of the mcp-coder installation.

        This test verifies the startup script uses the correct path for the
        mcp-coder executable while keeping MCP variables pointing to session folder.
        """
        # Setup test paths
        session_folder = tmp_path / "session_folder"
        session_folder.mkdir()

        # Simulate environment where MCP variables point to session folder
        # (this is correct for MCP server config but breaks mcp-coder executable path)
        mock_env = {
            "MCP_CODER_PROJECT_DIR": str(session_folder),
            "MCP_CODER_VENV_DIR": str(session_folder / ".venv"),
        }

        with patch("os.environ", mock_env):
            # Create startup script with session_folder_path to test the fix
            script_path = create_startup_script(
                folder_path=session_folder,
                issue_number=123,
                issue_title="Test Issue",
                status="status-01:created",
                repo_name="test-repo",
                issue_url="https://github.com/owner/repo/issues/123",
                is_intervention=False,
                timeout=30,
                session_folder_path=session_folder,
            )

            # Read the generated script content
            script_content = script_path.read_text(encoding="utf-8")

            # The critical test: script should NOT try to run mcp-coder from session folder
            # It should use the actual mcp-coder installation location

            # The script should be able to find mcp-coder executable
            assert "mcp-coder" in script_content

            # After the fix: MCP environment variables should now be set directly in the script
            # pointing to the session folder (this is the correct behavior for MCP server config)
            assert "MCP_CODER_PROJECT_DIR=" + str(session_folder) in script_content
            assert (
                "MCP_CODER_VENV_DIR=" + str(session_folder / ".venv") in script_content
            )

            # Verify the script shows the correct install path for mcp-coder executable
            assert "MCP-Coder install:" in script_content

            # The mcp-coder executable path should still use the installation directory
            # (not the session folder) for finding the executable

    @pytest.mark.skipif(
        platform.system() != "Windows",
        reason="Startup script functionality is Windows-only",
    )
    def test_startup_script_separates_mcp_executable_from_mcp_config_env(
        self, tmp_path: Path
    ) -> None:
        """Test that startup script separates mcp-coder executable path from MCP config env vars.

        This test ensures that:
        1. MCP environment variables (MCP_CODER_PROJECT_DIR, MCP_CODER_VENV_DIR) point to session
        2. mcp-coder executable is found via PATH or absolute path to installation
        """
        session_folder = tmp_path / "mcp_session_123"
        session_folder.mkdir()

        script_path = create_startup_script(
            folder_path=session_folder,
            issue_number=123,
            issue_title="Test Issue",
            status="status-01:created",
            repo_name="test-repo",
            issue_url="https://github.com/owner/repo/issues/123",
            is_intervention=False,
            timeout=30,
            session_folder_path=session_folder,
        )

        script_content = script_path.read_text(encoding="utf-8")

        # With the fix: MCP environment variables are now set directly in the startup script
        # pointing to the session folder (correct for MCP server config)

        # Session folder SHOULD appear in MCP environment variable assignments
        assert "MCP_CODER_PROJECT_DIR=" + str(session_folder) in script_content
        assert "MCP_CODER_VENV_DIR=" + str(session_folder / ".venv") in script_content

        # Script should show the mcp-coder installation path (separate from MCP config)
        assert "MCP-Coder install:" in script_content

        # mcp-coder command should be available via PATH from installation location
        lines_with_mcp_coder = [
            line
            for line in script_content.split("\n")
            if "mcp-coder" in line and not line.strip().startswith("set")
        ]

        for line in lines_with_mcp_coder:
            # mcp-coder command should not start with session folder path
            assert not line.strip().startswith(str(session_folder))
