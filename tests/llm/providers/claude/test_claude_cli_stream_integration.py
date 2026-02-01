#!/usr/bin/env python3
"""Integration tests for Claude CLI stream-json functionality.

These tests actually call the Claude CLI and verify stream logging works correctly.
They require:
- Claude CLI installed and authenticated
- Network access to Claude API

Run with: pytest -m claude_cli_integration
"""

import tempfile
from pathlib import Path

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    ask_claude_code_cli,
    parse_stream_json_file,
)


@pytest.mark.claude_cli_integration
class TestClaudeCliStreamIntegration:
    """Integration tests for Claude CLI with stream-json output."""

    def test_simple_question_creates_stream_file(self) -> None:
        """Test that a simple Claude question creates a valid stream log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Ask a simple question with short timeout
            result = ask_claude_code_cli(
                question="What is 2+2? Reply with just the number.",
                timeout=60,
                logs_dir=tmpdir,
            )

            # Verify response structure
            assert result["text"], "Expected non-empty response text"
            assert result["session_id"], "Expected session_id in response"
            assert result["method"] == "cli"
            assert result["provider"] == "claude"

            # Verify stream file was created
            stream_file = result["raw_response"].get("stream_file")
            assert stream_file, "Expected stream_file in raw_response"
            stream_file_path = Path(str(stream_file))
            assert stream_file_path.exists(), f"Stream file not found: {stream_file}"

            # Verify stream file content
            content = stream_file_path.read_text(encoding="utf-8")
            assert content, "Stream file should not be empty"

            # Parse and verify structure
            parsed = parse_stream_json_file(stream_file_path)
            assert parsed["session_id"] == result["session_id"]
            assert len(parsed["messages"]) >= 2  # At least system + result
            assert parsed["system_message"] is not None
            assert parsed["result_message"] is not None

    def test_stream_file_contains_cost_info(self) -> None:
        """Test that stream file contains cost and usage information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ask_claude_code_cli(
                question="Say 'hello' and nothing else.",
                timeout=60,
                logs_dir=tmpdir,
            )

            # Check cost info in response
            raw = result["raw_response"]
            assert "total_cost_usd" in raw, "Expected cost in response"
            assert "usage" in raw, "Expected usage in response"

            # Verify from stream file too
            stream_file = raw.get("stream_file")
            parsed = parse_stream_json_file(Path(str(stream_file)))

            result_msg = parsed["result_message"]
            assert result_msg is not None
            assert "total_cost_usd" in result_msg
            assert result_msg["total_cost_usd"] > 0

    def test_stream_file_logs_to_correct_directory(self) -> None:
        """Test that stream files are created in the specified logs directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "my_logs"
            logs_dir.mkdir()

            result = ask_claude_code_cli(
                question="Reply with 'ok'.",
                timeout=60,
                logs_dir=str(logs_dir),
            )

            # Verify stream file is in the right place
            stream_file = Path(str(result["raw_response"]["stream_file"]))
            assert logs_dir in stream_file.parents
            assert "claude-sessions" in str(stream_file)
            assert stream_file.suffix == ".ndjson"

    def test_session_continuity_with_stream_logging(self) -> None:
        """Test that session continuity works with stream logging enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First message
            result1 = ask_claude_code_cli(
                question="Remember: my favorite color is blue. Reply with 'noted'.",
                timeout=60,
                logs_dir=tmpdir,
            )

            session_id = result1["session_id"]
            assert session_id, "Expected session_id from first call"

            # Second message using same session
            result2 = ask_claude_code_cli(
                question="What is my favorite color? Reply with just the color.",
                session_id=session_id,
                timeout=60,
                logs_dir=tmpdir,
            )

            # Verify session was resumed
            assert result2["session_id"] == session_id

            # Verify response mentions blue
            assert "blue" in result2["text"].lower()

            # Verify we have 2 stream files
            session_dir = Path(tmpdir) / "claude-sessions"
            stream_files = list(session_dir.glob("*.ndjson"))
            assert len(stream_files) == 2

    def test_stream_file_created_on_success(self) -> None:
        """Test that stream file is created and contains valid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ask_claude_code_cli(
                question="Say 'done'.",
                timeout=60,
                logs_dir=tmpdir,
            )

            # Stream file should exist
            session_dir = Path(tmpdir) / "claude-sessions"
            stream_files = list(session_dir.glob("*.ndjson"))
            assert len(stream_files) == 1

            # File should have content
            content = stream_files[0].read_text(encoding="utf-8")
            assert len(content) > 0

            # Should have multiple lines (system, assistant, result)
            lines = [line for line in content.splitlines() if line.strip()]
            assert len(lines) >= 2


@pytest.mark.claude_cli_integration
class TestClaudeCliErrorDiagnosis:
    """Integration tests for error diagnosis via stream files."""

    def test_error_response_captured_in_stream(self) -> None:
        """Test that error responses are captured in stream file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # This should succeed but we test the structure
            result = ask_claude_code_cli(
                question="Say 'test'.",
                timeout=60,
                logs_dir=tmpdir,
            )

            # Verify error flag is captured
            stream_file = Path(str(result["raw_response"]["stream_file"]))
            parsed = parse_stream_json_file(stream_file)

            result_msg = parsed["result_message"]
            assert result_msg is not None
            assert "is_error" in result_msg
            assert result_msg["is_error"] is False  # Should be success

    def test_stream_file_contains_model_info(self) -> None:
        """Test that stream file contains model information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ask_claude_code_cli(
                question="Say 'hi'.",
                timeout=60,
                logs_dir=tmpdir,
            )

            stream_file = Path(str(result["raw_response"]["stream_file"]))
            parsed = parse_stream_json_file(stream_file)

            # System message should have model info
            sys_msg = parsed["system_message"]
            assert sys_msg is not None
            assert "model" in sys_msg
            model_value = sys_msg.get("model", "")
            assert isinstance(model_value, str)
            assert "claude" in model_value.lower()
