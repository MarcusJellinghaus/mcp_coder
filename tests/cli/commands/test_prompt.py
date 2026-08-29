"""Tests for prompt command functionality."""

import argparse
import json
import logging
from pathlib import Path
from typing import Any
from unittest import mock
from unittest.mock import Mock, mock_open, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt


def _make_text_events(
    text: str, session_id: str | None = None
) -> list[dict[str, object]]:
    """Create a minimal list of stream events for testing."""
    events: list[dict[str, object]] = [{"type": "text_delta", "text": text}]
    done_event: dict[str, object] = {"type": "done", "usage": {}}
    if session_id is not None:
        done_event["session_id"] = session_id
    events.append(done_event)
    return events


class TestSessionIdOutputFormat:
    """Tests for --output-format session-id functionality."""

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_session_id_format_returns_only_session_id(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """With --output-format session-id, prints only the session_id."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Response text here",
            "session_id": "abc123-session-id",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            mcp_config=None,
            settings=None,
        )

        result = execute_prompt(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "abc123-session-id"

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_session_id_format_error_when_no_session_id(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Returns error when response has no session_id."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Response text",
            "session_id": None,  # No session_id
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            mcp_config=None,
            settings=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_prompt(args)

        assert result == 1  # Error exit code
        assert "No session_id in response" in caplog.text

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_session_id_format_error_when_empty_session_id(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Returns error when response has empty session_id string."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Response text",
            "session_id": "",  # Empty session_id
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            mcp_config=None,
            settings=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_prompt(args)

        assert result == 1  # Error exit code
        assert "No session_id in response" in caplog.text

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_session_id_format_with_resume(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session ID format works when resuming existing session."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Continued response",
            "session_id": "existing-session-456",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="/discuss",
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id="existing-session-456",
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            mcp_config=None,
            settings=None,
        )

        result = execute_prompt(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "existing-session-456"
        # Verify session_id was passed to prompt_llm
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs["session_id"] == "existing-session-456"


class TestExecutePrompt:
    """Tests for execute_prompt function."""

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_basic_prompt_success(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful prompt execution with streaming."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("The capital of France is Paris.")
        )

        args = argparse.Namespace(
            prompt="What is the capital of France?",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        mock_prompt_llm_stream.assert_called_once_with(
            "What is the capital of France?",
            provider="claude",
            timeout=30,
            session_id=None,
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            mcp_config=None,
            settings_file=None,
            branch_name=mock.ANY,
            inject_prompts=False,
        )
        captured = capsys.readouterr()
        assert "The capital of France is Paris." in captured.out

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_prompt_api_error(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test API error handling when Claude API fails."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.side_effect = Exception("Claude API connection failed")
        args = argparse.Namespace(
            prompt="Test question",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_prompt(args)

        assert result == 1
        assert "Claude API connection failed" in caplog.text

    @patch("mcp_coder.cli.commands.prompt.mlflow_conversation")
    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_success(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        mock_mlflow_conversation: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful continuation from stored response file using session_id."""
        # Prevent mlflow_conversation from triggering tomllib.load on the
        # singleton's first init while builtins.open is mocked.
        mock_mlflow_conversation.return_value.__enter__.return_value = {
            "response_data": None,
            "error": None,
        }
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        stored_response = {"response_data": {"session_id": "previous-session-456"}}

        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(stored_response)
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Adding error handling.")
        )

        args = argparse.Namespace(
            prompt="Add error handling",
            continue_session_from="path/to/previous_response.json",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        mock_prompt_llm_stream.assert_called_once_with(
            "Add error handling",
            provider="claude",
            timeout=30,
            session_id="previous-session-456",
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            mcp_config=None,
            settings_file=None,
            branch_name=mock.ANY,
            inject_prompts=False,
        )
        captured = capsys.readouterr()
        assert "Adding error handling." in captured.out

    @patch("mcp_coder.llm.providers.langchain._load_langchain_config")
    @patch("mcp_coder.cli.commands.prompt.mlflow_conversation")
    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    def test_langchain_continue_from_non_session_stem_exits_1(
        self,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        mock_mlflow_conversation: Mock,
        mock_langchain_config: Mock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A langchain resume with no history file exits 1, naming id and path.

        Runs the real provider path (prompt_llm_stream is deliberately not
        mocked) so the guard in ask_langchain_stream is what fails the command.
        """
        mock_resolve_llm.return_value = ("langchain", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_mlflow_conversation.return_value.__enter__.return_value = {
            "response_data": None,
            "error": None,
        }
        # Truthy backend: without it the "backend not configured" error would
        # produce a false pass.
        mock_langchain_config.return_value = {
            "backend": "openai",
            "model": "gpt-4o-mini",
            "api_key": "k",
            "base_url": None,
            "api_version": None,
            "default_provider": None,
        }
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from=str(tmp_path / "response_2025-01-01T00-00-00.json"),
            llm_method="langchain",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_prompt(args)

        assert result == 1
        assert "response_2025-01-01T00-00-00" in caplog.text
        assert "response_2025-01-01T00-00-00.json" in caplog.text
        assert str(tmp_path) in caplog.text

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    @patch("os.path.exists")
    def test_continue_from_file_not_found(
        self,
        mock_exists: Mock,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when continue_from file doesn't exist."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_exists.return_value = False
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Starting new conversation.")
        )

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from="path/to/nonexistent_file.json",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        mock_prompt_llm_stream.assert_called_once_with(
            "Continue conversation",
            provider="claude",
            timeout=30,
            session_id=None,
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            mcp_config=None,
            settings_file=None,
            branch_name=mock.ANY,
            inject_prompts=False,
        )
        captured = capsys.readouterr()
        assert (
            "Warning: No session_id found" in captured.out
            or "starting new conversation" in captured.out.lower()
        )

    @patch("mcp_coder.cli.commands.prompt.mlflow_conversation")
    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_invalid_json(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        mock_mlflow_conversation: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when continue_from file contains invalid JSON."""
        # Prevent mlflow_conversation from triggering tomllib.load on the
        # singleton's first init while builtins.open is mocked.
        mock_mlflow_conversation.return_value.__enter__.return_value = {
            "response_data": None,
            "error": None,
        }
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = "{ invalid json content }"
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Starting new conversation.")
        )

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from="path/to/invalid.json",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        mock_prompt_llm_stream.assert_called_once_with(
            "Continue conversation",
            provider="claude",
            timeout=30,
            session_id=None,
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            mcp_config=None,
            settings_file=None,
            branch_name=mock.ANY,
            inject_prompts=False,
        )
        captured = capsys.readouterr()
        assert (
            "Warning: No session_id found" in captured.out
            or "starting new conversation" in captured.out.lower()
        )

    @patch("mcp_coder.cli.commands.prompt.mlflow_conversation")
    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_missing_session_id(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        mock_mlflow_conversation: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when continue_from file has missing session_id."""
        # Prevent mlflow_conversation from triggering tomllib.load on the
        # singleton's first init while builtins.open is mocked.
        mock_mlflow_conversation.return_value.__enter__.return_value = {
            "response_data": None,
            "error": None,
        }
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        incomplete_response = {"metadata": {"timestamp": "2025-09-19T10:30:00Z"}}

        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(incomplete_response)
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Starting new conversation.")
        )

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from="path/to/incomplete.json",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        mock_prompt_llm_stream.assert_called_once_with(
            "Continue conversation",
            provider="claude",
            timeout=30,
            session_id=None,
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            mcp_config=None,
            settings_file=None,
            branch_name=mock.ANY,
            inject_prompts=False,
        )
        # "Warning: No session_id found" now goes through logging, not stdout

    @patch("mcp_coder.cli.commands.prompt.mlflow_conversation")
    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_with_ndjson_format(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        mock_mlflow_conversation: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test continuation functionality works with ndjson output format."""
        # Prevent mlflow_conversation from triggering tomllib.load on the
        # singleton's first init while builtins.open is mocked.
        mock_mlflow_conversation.return_value.__enter__.return_value = {
            "response_data": None,
            "error": None,
        }
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        stored_response = {"response_data": {"session_id": "ndjson-session-123"}}

        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(stored_response)

        mock_prompt_llm_stream.return_value = iter(
            _make_text_events(
                "Here are some advanced Python features.",
                session_id="ndjson-session-new-456",
            )
        )

        args = argparse.Namespace(
            prompt="Tell me about advanced features",
            continue_session_from="path/to/previous.json",
            output_format="ndjson",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        mock_prompt_llm_stream.assert_called_once_with(
            "Tell me about advanced features",
            provider=mock.ANY,
            timeout=30,
            session_id="ndjson-session-123",
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            mcp_config=None,
            settings_file=None,
            branch_name=mock.ANY,
            inject_prompts=False,
        )
        captured = capsys.readouterr()
        # NDJSON format should output JSON lines
        assert "ndjson-session-new-456" in captured.out

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_execute_prompt_with_env_vars(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that env_vars are prepared and passed to prompt_llm_stream."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_env_vars = {
            "MCP_CODER_PROJECT_DIR": "/test/project",
            "MCP_CODER_VENV_DIR": "/test/project/.venv",
        }
        mock_prepare_env.return_value = mock_env_vars
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response with env vars.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        mock_prepare_env.assert_called_once()
        # Verify Path.cwd() was passed (check the call's first argument is a Path)
        call_args = mock_prepare_env.call_args[0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], Path)

        mock_prompt_llm_stream.assert_called_once_with(
            "Test prompt",
            provider="claude",
            timeout=30,
            session_id=None,
            env_vars=mock_env_vars,
            project_dir=mock.ANY,
            mcp_config=None,
            settings_file=None,
            branch_name=mock.ANY,
            inject_prompts=False,
        )
        captured = capsys.readouterr()
        assert "Response with env vars." in captured.out

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_execute_prompt_no_venv_graceful(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when no venv is found."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        # Simulate RuntimeError when no venv found
        mock_prepare_env.side_effect = RuntimeError("No virtual environment found")
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response without env vars.")
        )

        args = argparse.Namespace(
            prompt="Test prompt without venv",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        # Should still succeed
        assert result == 0
        mock_prepare_env.assert_called_once()

        # Should call prompt_llm_stream with env_vars=None
        mock_prompt_llm_stream.assert_called_once_with(
            "Test prompt without venv",
            provider="claude",
            timeout=30,
            session_id=None,
            env_vars=None,
            project_dir=mock.ANY,
            mcp_config=None,
            settings_file=None,
            branch_name=mock.ANY,
            inject_prompts=False,
        )
        captured = capsys.readouterr()
        assert "Response without env vars." in captured.out


class TestPromptClaudeCwd:
    """Tests for Claude working directory handling in prompt command."""

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_no_project_dir_falls_back_to_cwd(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No --project-dir: the subprocess cwd is the shell's CWD.

        This documents the no-``project_dir`` fallback, not the default. The
        default is ``project_dir`` (see ``test_claude_cwd_is_project_dir``
        below); this test only reaches the CWD because ``project_dir`` is None.
        """
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response from the working directory.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        # Verify the subprocess cwd was passed to prompt_llm_stream and is CWD
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert "project_dir" in call_kwargs
        assert call_kwargs["project_dir"] == str(Path.cwd())
        captured = capsys.readouterr()
        assert "Response from the working directory." in captured.out

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_claude_cwd_is_project_dir(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The subprocess cwd is --project-dir, not the shell's cwd."""
        project_dir = tmp_path / "repo"
        project_dir.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()

        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(project_dir)}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response from the project directory.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=str(project_dir),
        )

        # Stand outside the project directory: "from any shell working directory"
        # is half the acceptance criterion.
        monkeypatch.chdir(elsewhere)

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["project_dir"] == str(project_dir)
        assert call_kwargs["project_dir"] != str(Path.cwd())
        captured = capsys.readouterr()
        assert "Response from the project directory." in captured.out

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_claude_cwd_with_all_other_args(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Resolving the Claude cwd works with all other args (no conflicts)."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response with all args.")
        )

        project_dir = tmp_path / "project_dir"
        project_dir.mkdir()

        args = argparse.Namespace(
            prompt="Test prompt",
            project_dir=str(project_dir),
            timeout=60,
            llm_method="claude",
            output_format="text",
            session_id="test-session-123",
            mcp_config=None,
            settings=None,
        )

        result = execute_prompt(args)

        assert result == 0
        # Verify all arguments were passed correctly
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["project_dir"] == str(project_dir)
        assert call_kwargs["timeout"] == 60
        assert call_kwargs["session_id"] == "test-session-123"
        captured = capsys.readouterr()
        assert "Response with all args." in captured.out


class TestAddSystemPromptsFlag:
    """Tests for --add-system-prompts flag wiring."""

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_prompt_add_system_prompts_flag_injects_prompts(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When --add-system-prompts is set, inject_prompts=True reaches prompt_llm_stream."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response with prompts.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=True,
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["inject_prompts"] is True
        # project_dir is resolved from CWD since the project_dir arg is None
        assert call_kwargs["project_dir"] == str(Path.cwd())

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_prompt_no_flag_no_prompt_injection(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Without --add-system-prompts, inject_prompts=False is passed."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response without prompts.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=False,
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["inject_prompts"] is False

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_prompt_add_system_prompts_with_explicit_project_dir(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When --add-system-prompts is set with explicit --project-dir, that dir is used."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response with explicit project dir.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=True,
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=str(tmp_path),
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["inject_prompts"] is True
        assert call_kwargs["project_dir"] == str(tmp_path)

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_prompt_add_system_prompts_session_id_format(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Flag works with session-id output format (prompt_llm path)."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm.return_value = {
            "text": "response",
            "session_id": "sess-123",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=True,
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs["inject_prompts"] is True

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_prompt_add_system_prompts_json_format(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Flag works with json output format (prompt_llm path with branch_name)."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm.return_value = {
            "text": "response",
            "session_id": "sess-456",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=True,
            output_format="json",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            store_response=False,
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs["inject_prompts"] is True
