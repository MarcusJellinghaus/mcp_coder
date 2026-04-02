"""Test session continuation parameter priority."""

import argparse
import json
import logging
from typing import Any, Dict
from unittest.mock import Mock, mock_open, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt

# Common patches needed for all tests
_STREAM = "mcp_coder.cli.commands.prompt.prompt_llm_stream"
_RESOLVE_LLM = "mcp_coder.cli.commands.prompt.resolve_llm_method"
_PREPARE_ENV = "mcp_coder.cli.commands.prompt.prepare_llm_environment"
_RESOLVE_MCP = "mcp_coder.cli.commands.prompt.resolve_mcp_config_path"


def _stream_events(session_id: str = "test-session") -> list[dict[str, object]]:
    """Create minimal stream events for testing."""
    return [
        {"type": "text_delta", "text": "Response"},
        {"type": "done", "usage": {}, "session_id": session_id},
    ]


class TestSessionPriority:
    """Test priority order: --session-id > --continue-session-from > --continue-session."""

    @patch(_RESOLVE_MCP, return_value=None)
    @patch(_PREPARE_ENV, return_value={"MCP_CODER_PROJECT_DIR": "/test"})
    @patch(_RESOLVE_LLM, return_value=("claude", "cli"))
    @patch(_STREAM)
    def test_session_id_alone(
        self,
        mock_prompt_llm_stream: Mock,
        mock_llm: Mock,
        mock_env: Mock,
        mock_mcp: Mock,
    ) -> None:
        """Test --session-id is used when provided alone."""
        mock_prompt_llm_stream.return_value = iter(_stream_events("explicit-123"))

        args = argparse.Namespace(
            prompt="Test",
            session_id="explicit-123",
            continue_session_from=None,
            continue_session=False,
            llm_method="claude",
            mcp_config=None,
            project_dir=None,
        )

        execute_prompt(args)

        mock_prompt_llm_stream.assert_called_once()
        assert mock_prompt_llm_stream.call_args[1]["session_id"] == "explicit-123"

    @patch(_RESOLVE_MCP, return_value=None)
    @patch(_PREPARE_ENV, return_value={"MCP_CODER_PROJECT_DIR": "/test"})
    @patch(_RESOLVE_LLM, return_value=("claude", "cli"))
    @patch(_STREAM)
    @patch(
        "builtins.open",
        mock_open(read_data=json.dumps({"response_data": {"session_id": "file-456"}})),
    )
    @patch("os.path.exists", return_value=True)
    def test_session_id_overrides_continue_session_from(
        self,
        mock_exists: Mock,
        mock_prompt_llm_stream: Mock,
        mock_llm: Mock,
        mock_env: Mock,
        mock_mcp: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test --session-id takes priority over --continue-session-from."""
        mock_prompt_llm_stream.return_value = iter(_stream_events("explicit-123"))

        args = argparse.Namespace(
            prompt="Test",
            session_id="explicit-123",
            continue_session_from="file.json",
            continue_session=False,
            llm_method="claude",
            mcp_config=None,
            project_dir=None,
        )

        with caplog.at_level(logging.DEBUG):
            execute_prompt(args)

        mock_prompt_llm_stream.assert_called_once()
        assert mock_prompt_llm_stream.call_args[1]["session_id"] == "explicit-123"

        assert "Using explicit session ID" in caplog.text

    @patch(_RESOLVE_MCP, return_value=None)
    @patch(_PREPARE_ENV, return_value={"MCP_CODER_PROJECT_DIR": "/test"})
    @patch(_RESOLVE_LLM, return_value=("claude", "cli"))
    @patch(_STREAM)
    @patch("mcp_coder.llm.storage.find_latest_session")
    @patch(
        "builtins.open",
        mock_open(read_data=json.dumps({"response_data": {"session_id": "file-789"}})),
    )
    @patch("os.path.exists", return_value=True)
    def test_session_id_overrides_continue_session(
        self,
        mock_exists: Mock,
        mock_find: Mock,
        mock_prompt_llm_stream: Mock,
        mock_llm: Mock,
        mock_env: Mock,
        mock_mcp: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test --session-id takes priority over --continue-session."""
        mock_prompt_llm_stream.return_value = iter(_stream_events("explicit-123"))
        mock_find.return_value = "latest.json"

        args = argparse.Namespace(
            prompt="Test",
            session_id="explicit-123",
            continue_session_from=None,
            continue_session=True,
            llm_method="claude",
            mcp_config=None,
            project_dir=None,
        )

        with caplog.at_level(logging.DEBUG):
            execute_prompt(args)

        mock_prompt_llm_stream.assert_called_once()
        assert mock_prompt_llm_stream.call_args[1]["session_id"] == "explicit-123"

        assert "Using explicit session ID" in caplog.text

    @patch(_RESOLVE_MCP, return_value=None)
    @patch(_PREPARE_ENV, return_value={"MCP_CODER_PROJECT_DIR": "/test"})
    @patch(_RESOLVE_LLM, return_value=("claude", "cli"))
    @patch(_STREAM)
    @patch(
        "builtins.open",
        mock_open(read_data=json.dumps({"response_data": {"session_id": "file-456"}})),
    )
    @patch("os.path.exists", return_value=True)
    def test_continue_session_from_when_no_session_id(
        self,
        mock_exists: Mock,
        mock_prompt_llm_stream: Mock,
        mock_llm: Mock,
        mock_env: Mock,
        mock_mcp: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test --continue-session-from works when --session-id not provided."""
        mock_prompt_llm_stream.return_value = iter(_stream_events("file-456"))

        args = argparse.Namespace(
            prompt="Test",
            session_id=None,
            continue_session_from="file.json",
            continue_session=False,
            llm_method="claude",
            mcp_config=None,
            project_dir=None,
        )

        with caplog.at_level(logging.DEBUG):
            execute_prompt(args)

        mock_prompt_llm_stream.assert_called_once()
        assert mock_prompt_llm_stream.call_args[1]["session_id"] == "file-456"

        assert "Resuming session" in caplog.text

    @patch(_RESOLVE_MCP, return_value=None)
    @patch(_PREPARE_ENV, return_value={"MCP_CODER_PROJECT_DIR": "/test"})
    @patch(_RESOLVE_LLM, return_value=("claude", "cli"))
    @patch(_STREAM)
    @patch("mcp_coder.cli.commands.prompt.find_latest_session")
    @patch(
        "builtins.open",
        mock_open(read_data=json.dumps({"response_data": {"session_id": "file-789"}})),
    )
    @patch("os.path.exists", return_value=True)
    def test_continue_session_when_no_session_id(
        self,
        mock_exists: Mock,
        mock_find: Mock,
        mock_prompt_llm_stream: Mock,
        mock_llm: Mock,
        mock_env: Mock,
        mock_mcp: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test --continue-session works when --session-id not provided."""
        mock_prompt_llm_stream.return_value = iter(_stream_events("file-789"))
        mock_find.return_value = (
            ".mcp-coder/responses/response_2025-09-19T14-30-22.json"
        )

        args = argparse.Namespace(
            prompt="Test",
            session_id=None,
            continue_session_from=None,
            continue_session=True,
            llm_method="claude",
            mcp_config=None,
            project_dir=None,
        )

        with caplog.at_level(logging.DEBUG):
            execute_prompt(args)

        mock_prompt_llm_stream.assert_called_once()
        assert mock_prompt_llm_stream.call_args[1]["session_id"] == "file-789"

        assert "Resuming session" in caplog.text

    @patch(_RESOLVE_MCP, return_value=None)
    @patch(_PREPARE_ENV, return_value={"MCP_CODER_PROJECT_DIR": "/test"})
    @patch(_RESOLVE_LLM, return_value=("claude", "cli"))
    @patch(_STREAM)
    @patch("mcp_coder.cli.commands.prompt.find_latest_session", return_value=None)
    def test_continue_session_no_sessions_message_includes_store_response_hint(
        self,
        mock_find: Mock,
        mock_prompt_llm_stream: Mock,
        mock_llm: Mock,
        mock_env: Mock,
        mock_mcp: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify the message includes --store-response guidance."""
        mock_prompt_llm_stream.return_value = iter(_stream_events())

        args = argparse.Namespace(
            prompt="test",
            session_id=None,
            continue_session_from=None,
            continue_session=True,
            llm_method="claude",
            mcp_config=None,
            project_dir=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_prompt(args)

        assert result == 0
        assert "Save conversations with --store-response" in caplog.text
