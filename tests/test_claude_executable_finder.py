#!/usr/bin/env python3
"""Tests for claude_executable_finder module."""

import os
import shutil
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.claude_executable_finder import (
    _get_claude_search_paths,
    find_claude_executable,
    setup_claude_path,
    verify_claude_installation,
)


class TestGetClaudeSearchPaths:
    """Test the _get_claude_search_paths function."""

    @patch.dict(os.environ, {"USERNAME": "testuser"}, clear=True)
    @patch("mcp_coder.claude_executable_finder.shutil.which")
    def test_search_paths_generation(self, mock_which: Mock) -> None:  # type: ignore[misc]
        """Test that search paths are generated correctly."""
        mock_which.return_value = "/usr/bin/claude"  # type: ignore[attr-defined]

        paths = _get_claude_search_paths()

        # Should include shutil.which result
        assert "/usr/bin/claude" in paths

        # Should include Windows user-specific paths (using raw strings)
        assert r"C:\Users\testuser\.local\bin\claude.exe" in paths

        # Should include Unix-like paths
        assert any(".local/bin/claude" in path for path in paths)

        # Should include system paths
        assert "/usr/local/bin/claude" in paths

        # Should not include None values
        assert None not in paths

    @patch.dict(os.environ, {"USER": "unixuser"}, clear=True)
    @patch("mcp_coder.claude_executable_finder.shutil.which")
    def test_search_paths_unix_user(self, mock_which: Mock) -> None:  # type: ignore[misc]
        """Test search paths with Unix USER environment variable."""
        mock_which.return_value = None  # type: ignore[attr-defined]

        paths = _get_claude_search_paths()

        # Should use USER variable when USERNAME is not available
        assert r"C:\Users\unixuser\.local\bin\claude.exe" in paths


class TestFindClaudeExecutable:
    """Test the find_claude_executable function."""

    @patch("mcp_coder.claude_executable_finder._get_claude_search_paths")
    @patch("mcp_coder.claude_executable_finder.Path")
    def test_find_existing_executable(
        self, mock_path_class: MagicMock, mock_get_paths: MagicMock
    ) -> None:
        """Test finding an existing executable."""
        # Setup
        mock_get_paths.return_value = ["/usr/bin/claude", "/opt/claude/claude"]

        # Mock first path doesn't exist, second does
        mock_path1 = MagicMock()
        mock_path1.exists.return_value = False  # type: ignore[attr-defined]
        mock_path1.__str__.return_value = "/usr/bin/claude"  # type: ignore[attr-defined]

        mock_path2 = MagicMock()
        mock_path2.exists.return_value = True  # type: ignore[attr-defined]
        mock_path2.is_file.return_value = True  # type: ignore[attr-defined]
        mock_path2.__str__.return_value = "/opt/claude/claude"  # type: ignore[attr-defined]

        mock_path_class.side_effect = [mock_path1, mock_path2]

        # Mock os.access to return True for executable
        with patch("mcp_coder.claude_executable_finder.os.access", return_value=True):
            result = find_claude_executable(test_execution=False)

        # The function should return the string path, not the Path object
        assert result == "/opt/claude/claude"

    @patch("mcp_coder.claude_executable_finder._get_claude_search_paths")
    @patch("mcp_coder.claude_executable_finder.Path")
    def test_find_executable_with_execution_test(
        self, mock_path_class: MagicMock, mock_get_paths: MagicMock
    ) -> None:
        """Test finding executable with execution testing."""
        # Setup
        mock_get_paths.return_value = ["/usr/bin/claude"]

        mock_path = MagicMock()
        mock_path.exists.return_value = True  # type: ignore[attr-defined]
        mock_path.is_file.return_value = True  # type: ignore[attr-defined]
        mock_path.__str__.return_value = "/usr/bin/claude"  # type: ignore[attr-defined]
        mock_path_class.return_value = mock_path

        # Mock successful execution test
        mock_result = MagicMock()
        mock_result.return_code = 0  # type: ignore[attr-defined]

        with (
            patch("mcp_coder.claude_executable_finder.os.access", return_value=True),
            patch(
                "mcp_coder.claude_executable_finder.execute_command",
                return_value=mock_result,
            ),
        ):

            result = find_claude_executable(test_execution=True)

        assert result == "/usr/bin/claude"

    @patch("mcp_coder.claude_executable_finder._get_claude_search_paths")
    def test_find_executable_not_found_raises(self, mock_get_paths: MagicMock) -> None:
        """Test that FileNotFoundError is raised when executable not found."""
        mock_get_paths.return_value = []  # type: ignore[attr-defined]

        with pytest.raises(FileNotFoundError) as exc_info:
            find_claude_executable(return_none_if_not_found=False)

        assert "Claude Code CLI not found" in str(exc_info.value)

    @patch("mcp_coder.claude_executable_finder._get_claude_search_paths")
    def test_find_executable_not_found_returns_none(
        self, mock_get_paths: MagicMock
    ) -> None:
        """Test that None is returned when executable not found and return_none_if_not_found=True."""
        mock_get_paths.return_value = []

        result = find_claude_executable(return_none_if_not_found=True)

        assert result is None


class TestSetupClaudePath:
    """Test the setup_claude_path function."""

    @patch("mcp_coder.claude_executable_finder.shutil.which")
    def test_claude_already_in_path(self, mock_which: Mock) -> None:  # type: ignore[misc]
        """Test when Claude is already available in PATH."""
        mock_which.return_value = "/usr/bin/claude"  # type: ignore[attr-defined]

        result = setup_claude_path()

        assert result == "/usr/bin/claude"

    @patch("mcp_coder.claude_executable_finder.shutil.which")
    @patch("mcp_coder.claude_executable_finder.find_claude_executable")
    def test_add_claude_to_path(self, mock_find: MagicMock, mock_which: Mock) -> None:  # type: ignore[misc]
        """Test adding Claude directory to PATH."""
        # Store original PATH to restore later
        original_path = os.environ.get("PATH", "")

        try:
            # Set up test environment
            os.environ["PATH"] = "/usr/bin:/bin"

            # Claude not in PATH initially
            mock_which.return_value = None  # type: ignore[attr-defined]

            # But can be found in specific location
            mock_find.return_value = "/opt/claude/bin/claude"

            with patch("builtins.print") as mock_print:
                result = setup_claude_path()

            assert result == "/opt/claude/bin/claude"
            assert "/opt/claude/bin" in os.environ["PATH"]
            mock_print.assert_called_once_with("Added to PATH: /opt/claude/bin")

        finally:
            # Restore original PATH
            os.environ["PATH"] = original_path

    @patch("mcp_coder.claude_executable_finder.shutil.which")
    @patch("mcp_coder.claude_executable_finder.find_claude_executable")
    def test_claude_not_found(self, mock_find: MagicMock, mock_which: Mock) -> None:  # type: ignore[misc]
        """Test when Claude cannot be found."""
        mock_which.return_value = None  # type: ignore[attr-defined]
        mock_find.return_value = None

        result = setup_claude_path()

        assert result is None


class TestVerifyClaudeInstallation:
    """Test the verify_claude_installation function."""

    @patch("mcp_coder.claude_executable_finder.find_claude_executable")
    @patch("mcp_coder.claude_executable_finder.execute_command")
    def test_successful_verification(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
        """Test successful Claude installation verification."""
        # Setup
        mock_find.return_value = "/usr/bin/claude"  # type: ignore[attr-defined]

        mock_result = MagicMock()
        mock_result.return_code = 0  # type: ignore[attr-defined]
        mock_result.stdout = "claude 1.2.3"  # type: ignore[attr-defined]
        mock_execute.return_value = mock_result  # type: ignore[attr-defined]

        # Execute
        result = verify_claude_installation()

        # Verify
        assert result["found"] is True
        assert result["path"] == "/usr/bin/claude"
        assert result["version"] == "claude 1.2.3"
        assert result["works"] is True
        assert result["error"] is None

    @patch("mcp_coder.claude_executable_finder.find_claude_executable")
    def test_claude_not_found(self, mock_find: MagicMock) -> None:
        """Test verification when Claude is not found."""
        mock_find.side_effect = FileNotFoundError("Claude not found")  # type: ignore[attr-defined]

        result = verify_claude_installation()

        assert result["found"] is False
        assert result["path"] is None
        assert result["version"] is None
        assert result["works"] is False
        error_msg = result["error"]
        assert error_msg is not None
        assert "Claude not found" in error_msg  # pylint: disable=unsupported-membership-test

    @patch("mcp_coder.claude_executable_finder.find_claude_executable")
    @patch("mcp_coder.claude_executable_finder.execute_command")
    def test_version_check_fails(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
        """Test verification when version check fails."""
        # Setup
        mock_find.return_value = "/usr/bin/claude"

        mock_result = MagicMock()
        mock_result.return_code = 1  # type: ignore[attr-defined]
        mock_result.stderr = "Command failed"  # type: ignore[attr-defined]
        mock_execute.return_value = mock_result  # type: ignore[attr-defined]

        # Execute
        result = verify_claude_installation()

        # Verify
        assert result["found"] is True
        assert result["path"] == "/usr/bin/claude"
        assert result["version"] is None
        assert result["works"] is False
        error_msg = result["error"]
        assert error_msg is not None
        assert "Version check failed" in error_msg  # pylint: disable=unsupported-membership-test


class TestIntegration:
    """Integration tests for the claude_executable_finder module."""

    @pytest.mark.integration
    def test_real_claude_finder(self) -> None:
        """Test finding real Claude installation if available."""
        try:
            result = find_claude_executable(test_execution=True)
            assert isinstance(result, str)
            assert len(result) > 0
            print(f"Found Claude at: {result}")
        except FileNotFoundError:
            pytest.skip("Claude Code CLI not installed")

    @pytest.mark.integration
    def test_real_verification(self) -> None:
        """Test real Claude installation verification."""
        result = verify_claude_installation()

        assert isinstance(result, dict)
        assert "found" in result
        assert "works" in result

        if result["found"]:
            print(f"Claude found at: {result['path']}")
            print(f"Version: {result['version']}")
            print(f"Works: {result['works']}")
        else:
            print(f"Claude not found: {result['error']}")
            pytest.skip("Claude Code CLI not installed")
