"""Tests for logging_utils functions."""

import logging
import subprocess
from unittest.mock import Mock

import pytest

from mcp_coder.llm.providers.claude.logging_utils import (
    _MAX_OUTPUT_CHARS,
    log_llm_error,
    log_llm_request,
    log_llm_response,
)


@pytest.fixture
def caplog_debug(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Configure caplog to capture DEBUG level logs."""
    caplog.set_level(
        logging.DEBUG, logger="mcp_coder.llm.providers.claude.logging_utils"
    )
    return caplog


class TestLogLLMRequest:
    """Test log_llm_request function."""

    def test_log_llm_request_cli(self, caplog_debug: pytest.LogCaptureFixture) -> None:
        """Test logging CLI request with new session."""
        command = ["claude", "-p", "", "--output-format", "json"]

        log_llm_request(
            method="cli",
            provider="claude",
            session_id=None,
            prompt="What is the answer?",
            timeout=30,
            env_vars={"PATH": "/usr/bin"},
            cwd="/home/user",
            command=command,
            mcp_config=None,
        )

        log_output = caplog_debug.text
        assert "method=cli" in log_output
        assert "[new]" in log_output
        assert "What is the answer?" in log_output
        assert "command:" in log_output
        assert "30s" in log_output

    def test_log_llm_request_api_resuming(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test logging API request with resuming session."""
        log_llm_request(
            method="api",
            provider="claude",
            session_id="abc123",
            prompt="Remember this",
            timeout=60,
            env_vars={},
            cwd="/project",
            mcp_config=".mcp.json",
        )

        log_output = caplog_debug.text
        assert "method=api" in log_output
        assert "[resuming]" in log_output
        assert "Remember this" in log_output
        assert ".mcp.json" in log_output

    def test_log_llm_request_prompt_preview_short(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test prompt preview for short prompts."""
        log_llm_request(
            method="cli",
            provider="claude",
            session_id=None,
            prompt="Short",
            timeout=30,
            env_vars={},
            cwd="/home",
        )

        log_output = caplog_debug.text
        assert "5 chars - Short" in log_output

    def test_log_llm_request_prompt_preview_long(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test prompt preview for long prompts."""
        long_prompt = "x" * 500

        log_llm_request(
            method="cli",
            provider="claude",
            session_id=None,
            prompt=long_prompt,
            timeout=30,
            env_vars={},
            cwd="/home",
        )

        log_output = caplog_debug.text
        assert "500 chars -" in log_output
        assert "..." in log_output


class TestLogLLMResponse:
    """Test log_llm_response function."""

    def test_log_llm_response_cli(self, caplog_debug: pytest.LogCaptureFixture) -> None:
        """Test logging CLI response."""
        log_llm_response(
            method="cli",
            duration_ms=1500,
        )

        log_output = caplog_debug.text
        assert "method=cli" in log_output
        assert "1500ms" in log_output

    def test_log_llm_response_api_with_cost(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test logging API response with cost and usage."""
        usage = {"input_tokens": 100, "output_tokens": 50}

        log_llm_response(
            method="api",
            duration_ms=2000,
            cost_usd=0.0015,
            usage=usage,
            num_turns=3,
        )

        log_output = caplog_debug.text
        assert "method=api" in log_output
        assert "2000ms" in log_output
        assert "0.0015" in log_output
        assert "input_tokens" in log_output
        assert "output_tokens" in log_output
        assert "turns: 3" in log_output

    def test_log_llm_response_no_optional_fields(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test logging response with only required fields."""
        log_llm_response(
            method="cli",
            duration_ms=500,
        )

        log_output = caplog_debug.text
        assert "duration: 500ms" in log_output
        # Optional fields should not be in output
        assert "cost:" not in log_output
        assert "usage:" not in log_output


class TestLogLLMError:
    """Test log_llm_error function."""

    def test_log_llm_error_basic(self, caplog_debug: pytest.LogCaptureFixture) -> None:
        """Test logging error with basic info."""
        error = ValueError("Test error message")

        log_llm_error(
            method="cli",
            error=error,
        )

        log_output = caplog_debug.text
        assert "method=cli" in log_output
        assert "ValueError" in log_output
        assert "Test error message" in log_output

    def test_log_llm_error_with_duration(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test logging error with duration."""
        error = RuntimeError("Request failed")

        log_llm_error(
            method="api",
            error=error,
            duration_ms=1000,
        )

        log_output = caplog_debug.text
        assert "method=api" in log_output
        assert "RuntimeError" in log_output
        assert "Request failed" in log_output
        assert "1000ms" in log_output

    def test_log_llm_error_custom_exception(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test logging custom exception."""

        class CustomError(Exception):
            pass

        error = CustomError("Custom message")

        log_llm_error(
            method="cli",
            error=error,
        )

        log_output = caplog_debug.text
        assert "CustomError" in log_output
        assert "Custom message" in log_output

    def test_log_llm_error_called_process_error_with_stderr(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test logging CalledProcessError includes stderr."""
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["claude", "-p"],
            output="some stdout",
            stderr="Authentication failed: invalid token",
        )

        log_llm_error(
            method="cli",
            error=error,
            duration_ms=5000,
        )

        log_output = caplog_debug.text
        assert "CalledProcessError" in log_output
        assert "stderr: Authentication failed: invalid token" in log_output
        assert "stdout: some stdout" in log_output
        assert "5000ms" in log_output

    def test_log_llm_error_called_process_error_truncates_long_output(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test that long stderr/stdout is truncated."""
        long_stderr = "x" * (_MAX_OUTPUT_CHARS + 500)
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["claude", "-p"],
            stderr=long_stderr,
        )

        log_llm_error(
            method="cli",
            error=error,
        )

        log_output = caplog_debug.text
        assert "stderr:" in log_output
        assert "... (truncated)" in log_output
        # Should not contain the full long string
        assert long_stderr not in log_output

    def test_log_llm_error_called_process_error_empty_output(
        self, caplog_debug: pytest.LogCaptureFixture
    ) -> None:
        """Test CalledProcessError with empty stdout/stderr doesn't add extra lines."""
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["claude", "-p"],
            output="",
            stderr="",
        )

        log_llm_error(
            method="cli",
            error=error,
        )

        log_output = caplog_debug.text
        assert "CalledProcessError" in log_output
        # Empty strings should not produce stderr/stdout lines
        assert "stderr:" not in log_output
        assert "stdout:" not in log_output
