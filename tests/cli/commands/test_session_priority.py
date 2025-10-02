"""Test session continuation parameter priority."""

import argparse
import json
from unittest.mock import Mock, mock_open, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt


class TestSessionPriority:
    """Test priority order: --session-id > --continue-session-from > --continue-session."""

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_session_id_alone(self, mock_ask_llm: Mock) -> None:
        """Test --session-id is used when provided alone."""
        mock_ask_llm.return_value = "Response"

        args = argparse.Namespace(
            prompt="Test",
            session_id="explicit-123",
            continue_session_from=None,
            continue_session=False,
        )

        execute_prompt(args)

        mock_ask_llm.assert_called_once()
        assert mock_ask_llm.call_args[1]["session_id"] == "explicit-123"

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch(
        "builtins.open",
        mock_open(
            read_data=json.dumps(
                {"response_data": {"session_info": {"session_id": "file-456"}}}
            )
        ),
    )
    @patch("os.path.exists", return_value=True)
    def test_session_id_overrides_continue_session_from(
        self, mock_exists: Mock, mock_ask_llm: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test --session-id takes priority over --continue-session-from."""
        mock_ask_llm.return_value = "Response"

        args = argparse.Namespace(
            prompt="Test",
            session_id="explicit-123",
            continue_session_from="file.json",
            continue_session=False,
        )

        execute_prompt(args)

        # Should use explicit session_id, not file-based
        mock_ask_llm.assert_called_once()
        assert mock_ask_llm.call_args[1]["session_id"] == "explicit-123"

        # Should inform user
        captured = capsys.readouterr()
        assert "Using explicit session ID" in captured.out

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("mcp_coder.cli.commands.prompt._find_latest_response_file")
    @patch(
        "builtins.open",
        mock_open(
            read_data=json.dumps(
                {"response_data": {"session_info": {"session_id": "file-789"}}}
            )
        ),
    )
    @patch("os.path.exists", return_value=True)
    def test_session_id_overrides_continue_session(
        self,
        mock_exists: Mock,
        mock_find: Mock,
        mock_ask_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test --session-id takes priority over --continue-session."""
        mock_ask_llm.return_value = "Response"
        mock_find.return_value = "latest.json"

        args = argparse.Namespace(
            prompt="Test",
            session_id="explicit-123",
            continue_session_from=None,
            continue_session=True,
        )

        execute_prompt(args)

        # Should use explicit session_id, not file-based
        mock_ask_llm.assert_called_once()
        assert mock_ask_llm.call_args[1]["session_id"] == "explicit-123"

        # Should inform user
        captured = capsys.readouterr()
        assert "Using explicit session ID" in captured.out

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch(
        "builtins.open",
        mock_open(
            read_data=json.dumps(
                {"response_data": {"session_info": {"session_id": "file-456"}}}
            )
        ),
    )
    @patch("os.path.exists", return_value=True)
    def test_continue_session_from_when_no_session_id(
        self, mock_exists: Mock, mock_ask_llm: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test --continue-session-from works when --session-id not provided."""
        mock_ask_llm.return_value = "Response"

        args = argparse.Namespace(
            prompt="Test",
            session_id=None,
            continue_session_from="file.json",
            continue_session=False,
        )

        execute_prompt(args)

        # Should extract and use session from file
        mock_ask_llm.assert_called_once()
        assert mock_ask_llm.call_args[1]["session_id"] == "file-456"

        # Should show resumption message
        captured = capsys.readouterr()
        assert "Resuming session" in captured.out

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("mcp_coder.cli.commands.prompt.glob.glob")
    @patch(
        "builtins.open",
        mock_open(
            read_data=json.dumps(
                {"response_data": {"session_info": {"session_id": "file-789"}}}
            )
        ),
    )
    @patch("os.path.exists", return_value=True)
    def test_continue_session_when_no_session_id(
        self,
        mock_exists: Mock,
        mock_glob: Mock,
        mock_ask_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test --continue-session works when --session-id not provided."""
        mock_ask_llm.return_value = "Response"
        # Mock glob to return valid response files so _find_latest_response_file runs and prints
        mock_glob.return_value = [
            ".mcp-coder/responses/response_2025-09-19T14-30-22.json"
        ]

        args = argparse.Namespace(
            prompt="Test",
            session_id=None,
            continue_session_from=None,
            continue_session=True,
        )

        execute_prompt(args)

        # Should extract and use session from latest file
        mock_ask_llm.assert_called_once()
        assert mock_ask_llm.call_args[1]["session_id"] == "file-789"

        # Should show file discovery and resumption messages
        captured = capsys.readouterr()
        assert "Found" in captured.out and "previous sessions" in captured.out
        assert "Resuming session" in captured.out
