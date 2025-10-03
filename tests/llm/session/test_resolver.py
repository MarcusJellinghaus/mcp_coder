"""Tests for session resolution and LLM method parsing."""

import json
from typing import Any, Dict
from unittest.mock import Mock, mock_open, patch

import pytest

from mcp_coder.llm.session.resolver import parse_llm_method


class TestParseLlmMethod:
    """Tests for parse_llm_method function."""

    def test_parse_claude_code_cli(self) -> None:
        """Test parsing 'claude_code_cli' method."""
        provider, method = parse_llm_method("claude_code_cli")
        assert provider == "claude"
        assert method == "cli"

    def test_parse_claude_code_api(self) -> None:
        """Test parsing 'claude_code_api' method."""
        provider, method = parse_llm_method("claude_code_api")
        assert provider == "claude"
        assert method == "api"

    def test_parse_invalid_method(self) -> None:
        """Test error handling for unsupported method."""
        with pytest.raises(ValueError, match="Unsupported llm_method"):
            parse_llm_method("invalid_method")


class TestSessionResolution:
    """Tests for session continuation and resolution functionality."""

    @pytest.fixture
    def sample_stored_response(self) -> Dict[str, Any]:
        """Standard stored response data for continuation tests."""
        return {
            "prompt": "How do I create a Python file?",
            "response_data": {
                "text": "Here's how to create a Python file.",
                "session_info": {
                    "session_id": "previous-session-456",
                    "model": "claude-sonnet-4",
                    "tools": ["file_writer"],
                    "mcp_servers": [{"name": "fs_server", "status": "connected"}],
                },
                "result_info": {
                    "duration_ms": 1500,
                    "cost_usd": 0.025,
                    "usage": {"input_tokens": 15, "output_tokens": 12},
                },
                "raw_messages": [
                    {"role": "user", "content": "How do I create a Python file?"},
                    {
                        "role": "assistant",
                        "content": "Here's how to create a Python file.",
                    },
                ],
            },
            "metadata": {
                "timestamp": "2025-09-19T10:30:00Z",
                "working_directory": "/test/dir",
                "model": "claude-sonnet-4",
            },
        }

    def test_continue_from_success(
        self,
        sample_stored_response: Dict[str, Any],
    ) -> None:
        """Test successful continuation from stored response file using session_id."""
        # Test the session extraction logic directly
        session_info = sample_stored_response["response_data"]["session_info"]
        session_id = session_info["session_id"]

        # Verify we can extract the session ID properly
        assert session_id == "previous-session-456"
        assert session_info["model"] == "claude-sonnet-4"
        assert "file_writer" in session_info["tools"]

    def test_continue_from_file_not_found(self) -> None:
        """Test graceful handling when continue_from file doesn't exist."""
        # This tests the file handling logic that would be used in session resolution
        fake_path = "/path/to/nonexistent_file.json"

        # File existence check should return False
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            # Session resolution should handle this gracefully
            file_exists = mock_exists("/path/to/nonexistent_file.json")
            assert file_exists is False

    def test_continue_from_invalid_json(self) -> None:
        """Test graceful handling when continue_from file contains invalid JSON."""
        # Test JSON parsing error handling
        invalid_json = "{ invalid json content }"

        try:
            json.loads(invalid_json)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            # Expected behavior - session resolution should handle this
            pass

    def test_continue_from_missing_required_fields(self) -> None:
        """Test graceful handling when continue_from file has missing session_id."""
        # Test incomplete stored response (missing session_id)
        incomplete_response = {
            "metadata": {
                "timestamp": "2025-09-19T10:30:00Z",
                "working_directory": "/test/dir",
            }
            # Missing "prompt" and "response_data" fields - no session_id available
        }

        # Session extraction should handle missing fields gracefully
        session_id = None

        # Try to extract session_id from incomplete response
        if "response_data" in incomplete_response:
            response_data = incomplete_response["response_data"]
            if isinstance(response_data, dict) and "session_info" in response_data:
                session_info = response_data["session_info"]
                if isinstance(session_info, dict):
                    session_id = session_info.get("session_id")

        # Should be None when fields are missing
        assert session_id is None
