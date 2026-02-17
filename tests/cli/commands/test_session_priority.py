"""Test session continuation parameter priority."""

import argparse
import json
from typing import Any, Dict
from unittest.mock import Mock, mock_open, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt


def _llm_response(session_id: str = "test-session") -> Dict[str, Any]:
    return {
        "text": "Response",
        "session_id": session_id,
        "version": "1.0",
        "timestamp": "2024-01-01T00:00:00",
        "method": "api",
        "provider": "claude",
        "raw_response": {},
    }


class TestSessionPriority:
    """Test priority order: --session-id > --continue-session-from > --continue-session."""

    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_session_id_alone(self, mock_prompt_llm: Mock) -> None:
        """Test --session-id is used when provided alone."""
        mock_prompt_llm.return_value = _llm_response("explicit-123")

        args = argparse.Namespace(
            prompt="Test",
            session_id="explicit-123",
            continue_session_from=None,
            continue_session=False,
        )

        execute_prompt(args)

        mock_prompt_llm.assert_called_once()
        assert mock_prompt_llm.call_args[1]["session_id"] == "explicit-123"

    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    @patch(
        "builtins.open",
        mock_open(read_data=json.dumps({"response_data": {"session_id": "file-456"}})),
    )
    @patch("os.path.exists", return_value=True)
    def test_session_id_overrides_continue_session_from(
        self,
        mock_exists: Mock,
        mock_prompt_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test --session-id takes priority over --continue-session-from."""
        mock_prompt_llm.return_value = _llm_response("explicit-123")

        args = argparse.Namespace(
            prompt="Test",
            session_id="explicit-123",
            continue_session_from="file.json",
            continue_session=False,
        )

        execute_prompt(args)

        mock_prompt_llm.assert_called_once()
        assert mock_prompt_llm.call_args[1]["session_id"] == "explicit-123"

        captured = capsys.readouterr()
        assert "Using explicit session ID" in captured.out

    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
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
        mock_prompt_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test --session-id takes priority over --continue-session."""
        mock_prompt_llm.return_value = _llm_response("explicit-123")
        mock_find.return_value = "latest.json"

        args = argparse.Namespace(
            prompt="Test",
            session_id="explicit-123",
            continue_session_from=None,
            continue_session=True,
        )

        execute_prompt(args)

        mock_prompt_llm.assert_called_once()
        assert mock_prompt_llm.call_args[1]["session_id"] == "explicit-123"

        captured = capsys.readouterr()
        assert "Using explicit session ID" in captured.out

    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    @patch(
        "builtins.open",
        mock_open(read_data=json.dumps({"response_data": {"session_id": "file-456"}})),
    )
    @patch("os.path.exists", return_value=True)
    def test_continue_session_from_when_no_session_id(
        self,
        mock_exists: Mock,
        mock_prompt_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test --continue-session-from works when --session-id not provided."""
        mock_prompt_llm.return_value = _llm_response("file-456")

        args = argparse.Namespace(
            prompt="Test",
            session_id=None,
            continue_session_from="file.json",
            continue_session=False,
        )

        execute_prompt(args)

        mock_prompt_llm.assert_called_once()
        assert mock_prompt_llm.call_args[1]["session_id"] == "file-456"

        captured = capsys.readouterr()
        assert "Resuming session" in captured.out

    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
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
        mock_prompt_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test --continue-session works when --session-id not provided."""
        mock_prompt_llm.return_value = _llm_response("file-789")
        mock_find.return_value = (
            ".mcp-coder/responses/response_2025-09-19T14-30-22.json"
        )

        args = argparse.Namespace(
            prompt="Test",
            session_id=None,
            continue_session_from=None,
            continue_session=True,
        )

        execute_prompt(args)

        mock_prompt_llm.assert_called_once()
        assert mock_prompt_llm.call_args[1]["session_id"] == "file-789"

        captured = capsys.readouterr()
        assert "Resuming session" in captured.out
