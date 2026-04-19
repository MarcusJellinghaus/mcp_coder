"""Tests for the shared executable finder utility."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.executable_finder import find_executable


class TestFindExecutable:
    """Tests for find_executable()."""

    @patch("mcp_coder.utils.executable_finder.shutil.which")
    def test_find_executable_found(self, mock_which: MagicMock) -> None:
        """Mock shutil.which returning a path, verify it's returned."""
        mock_which.return_value = "/usr/bin/copilot"
        result = find_executable("copilot", install_hint="Install copilot")
        assert result == "/usr/bin/copilot"

    @patch("mcp_coder.utils.executable_finder.shutil.which")
    def test_find_executable_not_found(self, mock_which: MagicMock) -> None:
        """Mock shutil.which returning None, verify FileNotFoundError."""
        mock_which.return_value = None
        with pytest.raises(FileNotFoundError):
            find_executable("copilot", install_hint="Install copilot")

    @patch("mcp_coder.utils.executable_finder.shutil.which")
    def test_find_executable_not_found_message_contains_name(
        self, mock_which: MagicMock
    ) -> None:
        """Verify error mentions the executable name."""
        mock_which.return_value = None
        with pytest.raises(FileNotFoundError, match="copilot"):
            find_executable("copilot", install_hint="Install copilot")

    @patch("mcp_coder.utils.executable_finder.shutil.which")
    def test_find_executable_not_found_message_contains_hint(
        self, mock_which: MagicMock
    ) -> None:
        """Verify error includes the install_hint."""
        mock_which.return_value = None
        with pytest.raises(FileNotFoundError, match="Run npm install -g copilot"):
            find_executable("copilot", install_hint="Run npm install -g copilot")

    @patch("mcp_coder.utils.executable_finder.platform.system")
    @patch("mcp_coder.utils.executable_finder.shutil.which")
    def test_find_executable_windows_exe_fallback(
        self, mock_which: MagicMock, mock_system: MagicMock
    ) -> None:
        """On Windows, tries name.exe if name not found."""
        mock_system.return_value = "Windows"
        mock_which.side_effect = lambda n: (
            "C:\\Program Files\\copilot.exe" if n == "copilot.exe" else None
        )
        result = find_executable("copilot", install_hint="Install copilot")
        assert result == "C:\\Program Files\\copilot.exe"
