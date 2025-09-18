#!/usr/bin/env python3
"""Tests for enhanced error handling in claude_code_api module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm_providers.claude.claude_code_api import (
    _extract_real_error_message,
    _retry_with_backoff,
    _verify_claude_before_use,
    ask_claude_code_api,
)


class TestExtractRealErrorMessage:
    """Test the _extract_real_error_message function."""

    def test_windows_path_length_error(self) -> None:
        """Test extraction of Windows path length error."""
        # Create nested exception chain simulating the real error
        inner_error = OSError("[WinError 206] The filename or extension is too long")
        middle_error = RuntimeError("Process execution failed")
        middle_error.__cause__ = inner_error
        outer_error = Exception("SDK request failed")
        outer_error.__cause__ = middle_error

        result = _extract_real_error_message(outer_error)

        assert "Windows path length limit exceeded (WinError 206)" in result
        assert "current working directory path is very long" in result

    def test_cli_not_found_error(self) -> None:
        """Test extraction of CLINotFoundError."""
        from claude_code_sdk._errors import CLINotFoundError

        inner_error = CLINotFoundError(
            "Claude Code not found at: C:\\Users\\test\\.local\\bin\\claude.EXE"
        )
        outer_error = RuntimeError("Connection failed")
        outer_error.__cause__ = inner_error

        result = _extract_real_error_message(outer_error)

        assert "Claude CLI executable not found" in result
        assert "Claude Code not found at:" in result

    def test_file_not_found_error(self) -> None:
        """Test extraction of FileNotFoundError."""
        inner_error = FileNotFoundError("No such file or directory: 'claude'")
        outer_error = RuntimeError("Failed to execute")
        outer_error.__cause__ = inner_error

        result = _extract_real_error_message(outer_error)

        assert "File/executable not found" in result
        assert "No such file or directory" in result

    def test_permission_error(self) -> None:
        """Test extraction of PermissionError."""
        inner_error = PermissionError("Permission denied")
        outer_error = RuntimeError("Access failed")
        outer_error.__cause__ = inner_error

        result = _extract_real_error_message(outer_error)

        assert "Permission denied" in result

    def test_simple_error_no_nesting(self) -> None:
        """Test handling of simple error without nesting."""
        error = RuntimeError("Simple error message")

        result = _extract_real_error_message(error)

        assert result == "Simple error message"

    def test_deep_nesting_prevents_infinite_loop(self) -> None:
        """Test that deep exception nesting doesn't cause infinite loops."""
        # Create a chain of 10 exceptions
        error = RuntimeError("Deep error")
        current = error

        for i in range(9):
            next_error = RuntimeError(f"Level {i}")
            next_error.__cause__ = current
            current = next_error

        result = _extract_real_error_message(current)

        # Should complete without hanging and return some result
        assert isinstance(result, str)
        assert len(result) > 0


class TestRetryWithBackoff:
    """Test the _retry_with_backoff function."""

    def test_success_on_first_attempt(self) -> None:
        """Test that function succeeds on first attempt."""

        def successful_func() -> str:
            return "success"

        result = _retry_with_backoff(successful_func, max_retries=3, base_delay=0.1)

        assert result == "success"

    def test_success_after_retries(self) -> None:
        """Test that function succeeds after some retries."""
        call_count = 0

        def eventually_successful_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Temporary failure")
            return "success"

        result = _retry_with_backoff(
            eventually_successful_func, max_retries=3, base_delay=0.01
        )

        assert result == "success"
        assert call_count == 3

    def test_all_attempts_fail(self) -> None:
        """Test behavior when all attempts fail."""

        def always_failing_func() -> str:
            raise RuntimeError("Persistent failure")

        with pytest.raises(RuntimeError) as exc_info:
            _retry_with_backoff(always_failing_func, max_retries=2, base_delay=0.01)

        assert "Persistent failure" in str(exc_info.value)

    def test_zero_retries(self) -> None:
        """Test behavior with zero retries (single attempt)."""
        call_count = 0

        def counting_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("First attempt fails")
            return "success"

        with pytest.raises(RuntimeError):
            _retry_with_backoff(counting_func, max_retries=0, base_delay=0.01)

        assert call_count == 1


class TestVerifyClaudeBeforeUse:
    """Test the _verify_claude_before_use function."""

    @patch("mcp_coder.llm_providers.claude.claude_code_api.setup_claude_path")
    @patch("mcp_coder.llm_providers.claude.claude_code_api.verify_claude_installation")
    def test_successful_verification(
        self, mock_verify: MagicMock, mock_setup: MagicMock
    ) -> None:
        """Test successful Claude verification."""
        mock_setup.return_value = "/usr/local/bin/claude"
        mock_verify.return_value = {
            "found": True,
            "works": True,
            "path": "/usr/local/bin/claude",
            "version": "1.0.0",
            "error": None,
        }

        success, path, error = _verify_claude_before_use()

        assert success is True
        assert path == "/usr/local/bin/claude"
        assert error is None

    @patch("mcp_coder.llm_providers.claude.claude_code_api.setup_claude_path")
    @patch("mcp_coder.llm_providers.claude.claude_code_api.verify_claude_installation")
    def test_failed_verification(
        self, mock_verify: MagicMock, mock_setup: MagicMock
    ) -> None:
        """Test failed Claude verification."""
        mock_setup.return_value = None
        mock_verify.return_value = {
            "found": False,
            "works": False,
            "path": None,
            "error": "Claude CLI not found",
        }

        success, path, error = _verify_claude_before_use()

        assert success is False
        assert path is None
        assert error == "Claude CLI not found"

    @patch("mcp_coder.llm_providers.claude.claude_code_api.setup_claude_path")
    @patch("mcp_coder.llm_providers.claude.claude_code_api.verify_claude_installation")
    def test_setup_path_exception(
        self, mock_verify: MagicMock, mock_setup: MagicMock
    ) -> None:
        """Test behavior when setup_claude_path raises an exception."""
        mock_setup.side_effect = RuntimeError("Path setup failed")
        mock_verify.return_value = {
            "found": True,
            "works": True,
            "path": "/usr/local/bin/claude",
            "error": None,
        }

        success, path, error = _verify_claude_before_use()

        # Should still succeed if verification works despite path setup failure
        assert success is True
        assert path == "/usr/local/bin/claude"
        assert error is None


class TestAskClaudeCodeApiErrorHandling:
    """Test enhanced error handling in ask_claude_code_api function."""

    @patch("mcp_coder.llm_providers.claude.claude_code_api._retry_with_backoff")
    def test_windows_path_length_error_handling(self, mock_retry: MagicMock) -> None:
        """Test specific handling of Windows path length errors."""
        # Simulate WinError 206
        inner_error = OSError("[WinError 206] The filename or extension is too long")
        mock_retry.side_effect = inner_error

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            ask_claude_code_api("test question")

        error_msg = exc_info.value.stderr
        assert "Windows path length limit exceeded" in error_msg
        assert "Move your project to a shorter path" in error_msg
        assert "Enable long path support" in error_msg

    @patch("mcp_coder.llm_providers.claude.claude_code_api._retry_with_backoff")
    @patch("mcp_coder.llm_providers.claude.claude_code_api.find_claude_executable")
    def test_cli_not_found_error_with_path_found(
        self, mock_find: MagicMock, mock_retry: MagicMock
    ) -> None:
        """Test CLINotFoundError handling when Claude path can be found."""
        from claude_code_sdk._errors import CLINotFoundError

        mock_retry.side_effect = CLINotFoundError("Claude Code not found")
        mock_find.return_value = "C:\\Users\\test\\.local\\bin\\claude.exe"

        with patch.dict("os.environ", {"USERNAME": "testuser"}):
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                ask_claude_code_api("test question")

        error_msg = exc_info.value.stderr
        assert "Claude CLI found at:" in error_msg
        assert "Add Claude to your PATH" in error_msg
        assert "testuser" in error_msg  # Dynamic username

    @patch("mcp_coder.llm_providers.claude.claude_code_api._retry_with_backoff")
    @patch("mcp_coder.llm_providers.claude.claude_code_api.find_claude_executable")
    def test_cli_not_found_error_without_path_found(
        self, mock_find: MagicMock, mock_retry: MagicMock
    ) -> None:
        """Test CLINotFoundError handling when Claude path cannot be found."""
        from claude_code_sdk._errors import CLINotFoundError

        mock_retry.side_effect = CLINotFoundError("Claude Code not found")
        mock_find.return_value = None

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            ask_claude_code_api("test question")

        error_msg = exc_info.value.stderr
        assert "Install Claude CLI" in error_msg
        assert "npm install -g @anthropic-ai/claude-code" in error_msg

    @patch("mcp_coder.llm_providers.claude.claude_code_api._retry_with_backoff")
    def test_file_not_found_error_handling(self, mock_retry: MagicMock) -> None:
        """Test FileNotFoundError handling."""
        mock_retry.side_effect = FileNotFoundError("No such file or directory")

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            ask_claude_code_api("test question")

        error_msg = exc_info.value.stderr
        assert (
            "File/executable not found" in error_msg
        )  # Fixed: matches actual implementation
        assert "Verify Claude CLI is installed" in error_msg

    @patch("mcp_coder.llm_providers.claude.claude_code_api._retry_with_backoff")
    def test_permission_error_handling(self, mock_retry: MagicMock) -> None:
        """Test PermissionError handling."""
        mock_retry.side_effect = PermissionError("Permission denied")

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            ask_claude_code_api("test question")

        error_msg = exc_info.value.stderr
        assert "Permission denied" in error_msg
        assert "Run terminal as Administrator" in error_msg

    @patch("mcp_coder.llm_providers.claude.claude_code_api._retry_with_backoff")
    def test_timeout_error_passthrough(self, mock_retry: MagicMock) -> None:
        """Test that timeout errors are passed through without modification."""
        timeout_error = subprocess.TimeoutExpired(["claude"], 30, "Timeout")
        mock_retry.side_effect = timeout_error

        with pytest.raises(subprocess.TimeoutExpired):
            ask_claude_code_api("test question")

    @patch("mcp_coder.llm_providers.claude.claude_code_api._retry_with_backoff")
    def test_value_error_passthrough(self, mock_retry: MagicMock) -> None:
        """Test that ValueError is passed through without modification."""
        value_error = ValueError("Invalid input")
        mock_retry.side_effect = value_error

        with pytest.raises(ValueError):
            ask_claude_code_api("test question")

    @patch("mcp_coder.llm_providers.claude.claude_code_api._retry_with_backoff")
    def test_retry_logic_called(self, mock_retry: MagicMock) -> None:
        """Test that retry logic is properly called."""
        mock_retry.return_value = "success"

        result = ask_claude_code_api("test question")

        assert result == "success"
        mock_retry.assert_called_once()
        # Check that the retry was called with correct parameters
        args, kwargs = mock_retry.call_args
        assert len(args) == 1  # The function to retry
        assert kwargs.get("max_retries") == 2
        assert kwargs.get("base_delay") == 0.5
