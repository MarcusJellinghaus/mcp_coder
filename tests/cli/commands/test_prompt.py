"""Tests for prompt command functionality."""

import argparse
import json
from pathlib import Path
from typing import Any
from unittest import mock
from unittest.mock import Mock, mock_open, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt


class TestSessionIdOutputFormat:
    """Tests for --output-format session-id functionality."""

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.llm.interface.prompt_llm")
    def test_session_id_format_returns_only_session_id(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """With --output-format session-id, prints only the session_id."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Response text here",
            "session_id": "abc123-session-id",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude_code_api",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            execution_dir=None,
            mcp_config=None,
        )

        result = execute_prompt(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "abc123-session-id"

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.llm.interface.prompt_llm")
    def test_session_id_format_error_when_no_session_id(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Returns error when response has no session_id."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Response text",
            "session_id": None,  # No session_id
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude_code_api",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            execution_dir=None,
            mcp_config=None,
        )

        result = execute_prompt(args)

        assert result == 1  # Error exit code
        captured = capsys.readouterr()
        assert "Error: No session_id in response" in captured.err

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.llm.interface.prompt_llm")
    def test_session_id_format_error_when_empty_session_id(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Returns error when response has empty session_id string."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Response text",
            "session_id": "",  # Empty session_id
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude_code_api",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            execution_dir=None,
            mcp_config=None,
        )

        result = execute_prompt(args)

        assert result == 1  # Error exit code
        captured = capsys.readouterr()
        assert "Error: No session_id in response" in captured.err

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.llm.interface.prompt_llm")
    def test_session_id_format_with_resume(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session ID format works when resuming existing session."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Continued response",
            "session_id": "existing-session-456",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="/discuss",
            output_format="session-id",
            timeout=30,
            llm_method="claude_code_api",
            session_id="existing-session-456",
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            execution_dir=None,
            mcp_config=None,
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

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_basic_prompt_success(
        self,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful prompt execution with mocked ask_llm function."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_ask_llm.return_value = "The capital of France is Paris."
        args = argparse.Namespace(prompt="What is the capital of France?")

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "What is the capital of France?",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            execution_dir=mock.ANY,
            mcp_config=None,
            branch_name=mock.ANY,
        )
        captured = capsys.readouterr()
        assert "The capital of France is Paris." in captured.out

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_prompt_api_error(
        self,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test API error handling when Claude API fails."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_ask_llm.side_effect = Exception("Claude API connection failed")
        args = argparse.Namespace(prompt="Test question")

        result = execute_prompt(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "Claude API connection failed" in captured.err

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_success(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful continuation from stored response file using session_id."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        stored_response = {
            "response_data": {"session_info": {"session_id": "previous-session-456"}}
        }

        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(stored_response)
        mock_ask_llm.return_value = "Adding error handling."

        args = argparse.Namespace(
            prompt="Add error handling",
            continue_session_from="path/to/previous_response.json",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "Add error handling",
            provider="claude",
            method="api",
            timeout=30,
            session_id="previous-session-456",
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            execution_dir=mock.ANY,
            mcp_config=None,
            branch_name=mock.ANY,
        )
        captured = capsys.readouterr()
        assert "Adding error handling." in captured.out
        assert "Resuming session: previous-session" in captured.out

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("os.path.exists")
    def test_continue_from_file_not_found(
        self,
        mock_exists: Mock,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when continue_from file doesn't exist."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_exists.return_value = False
        mock_ask_llm.return_value = "Starting new conversation."

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from="path/to/nonexistent_file.json",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "Continue conversation",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            execution_dir=mock.ANY,
            mcp_config=None,
            branch_name=mock.ANY,
        )
        captured = capsys.readouterr()
        assert (
            "Warning: No session_id found" in captured.out
            or "starting new conversation" in captured.out.lower()
        )

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_invalid_json(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when continue_from file contains invalid JSON."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = "{ invalid json content }"
        mock_ask_llm.return_value = "Starting new conversation."

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from="path/to/invalid.json",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "Continue conversation",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            execution_dir=mock.ANY,
            mcp_config=None,
            branch_name=mock.ANY,
        )
        captured = capsys.readouterr()
        assert (
            "Warning: No session_id found" in captured.out
            or "starting new conversation" in captured.out.lower()
        )

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_missing_session_id(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when continue_from file has missing session_id."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        incomplete_response = {"metadata": {"timestamp": "2025-09-19T10:30:00Z"}}

        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(incomplete_response)
        mock_ask_llm.return_value = "Starting new conversation."

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from="path/to/incomplete.json",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "Continue conversation",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
            env_vars={"MCP_CODER_PROJECT_DIR": "/test"},
            project_dir=mock.ANY,
            execution_dir=mock.ANY,
            mcp_config=None,
            branch_name=mock.ANY,
        )
        captured = capsys.readouterr()
        assert "Warning: No session_id found" in captured.out

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_with_verbose_output(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_claude: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test continuation functionality works with verbose verbosity."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        stored_response = {
            "response_data": {
                "session_info": {"session_id": "verbose-continuation-123"}
            }
        }

        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(stored_response)

        new_response = {
            "text": "Here are some advanced Python features.",
            "session_info": {"session_id": "verbose-continuation-new-456"},
            "result_info": {"duration_ms": 2500, "cost_usd": 0.040},
        }
        mock_ask_claude.return_value = new_response

        args = argparse.Namespace(
            prompt="Tell me about advanced features",
            continue_session_from="path/to/previous.json",
            verbosity="verbose",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_claude.assert_called_once_with(
            "Tell me about advanced features",
            30,
            "verbose-continuation-123",
            {"MCP_CODER_PROJECT_DIR": "/test"},
            mock.ANY,
        )
        captured = capsys.readouterr()
        assert "Here are some advanced Python features." in captured.out
        assert "verbose-continuation-new-456" in captured.out

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_execute_prompt_with_env_vars(
        self,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that env_vars are prepared and passed to ask_llm."""
        mock_env_vars = {
            "MCP_CODER_PROJECT_DIR": "/test/project",
            "MCP_CODER_VENV_DIR": "/test/project/.venv",
        }
        mock_prepare_env.return_value = mock_env_vars
        mock_ask_llm.return_value = "Response with env vars."

        args = argparse.Namespace(prompt="Test prompt")

        result = execute_prompt(args)

        assert result == 0
        mock_prepare_env.assert_called_once()
        # Verify Path.cwd() was passed (check the call's first argument is a Path)
        call_args = mock_prepare_env.call_args[0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], Path)

        mock_ask_llm.assert_called_once_with(
            "Test prompt",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
            env_vars=mock_env_vars,
            project_dir=mock.ANY,
            execution_dir=mock.ANY,
            mcp_config=None,
            branch_name=mock.ANY,
        )
        captured = capsys.readouterr()
        assert "Response with env vars." in captured.out

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_execute_prompt_no_venv_graceful(
        self,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when no venv is found."""
        # Simulate RuntimeError when no venv found
        mock_prepare_env.side_effect = RuntimeError("No virtual environment found")
        mock_ask_llm.return_value = "Response without env vars."

        args = argparse.Namespace(prompt="Test prompt without venv")

        result = execute_prompt(args)

        # Should still succeed
        assert result == 0
        mock_prepare_env.assert_called_once()

        # Should call ask_llm with env_vars=None
        mock_ask_llm.assert_called_once_with(
            "Test prompt without venv",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
            env_vars=None,
            project_dir=mock.ANY,
            execution_dir=mock.ANY,
            mcp_config=None,
            branch_name=mock.ANY,
        )
        captured = capsys.readouterr()
        assert "Response without env vars." in captured.out


class TestPromptExecutionDir:
    """Tests for execution_dir handling in prompt command."""

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_default_execution_dir_uses_cwd(
        self,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test default execution_dir should use current working directory."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_ask_llm.return_value = "Response with default execution_dir."

        args = argparse.Namespace(
            prompt="Test prompt",
            execution_dir=None,  # No explicit execution_dir
        )

        result = execute_prompt(args)

        assert result == 0
        # Verify execution_dir was passed to ask_llm and equals CWD
        call_kwargs = mock_ask_llm.call_args[1]
        assert "execution_dir" in call_kwargs
        assert call_kwargs["execution_dir"] == str(Path.cwd())
        captured = capsys.readouterr()
        assert "Response with default execution_dir." in captured.out

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_explicit_execution_dir_absolute(
        self,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test explicit absolute execution_dir should be validated and used."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_ask_llm.return_value = "Response with explicit execution_dir."

        # Create a valid temporary directory
        execution_dir = tmp_path / "exec_dir"
        execution_dir.mkdir()

        args = argparse.Namespace(
            prompt="Test prompt",
            execution_dir=str(execution_dir),
        )

        result = execute_prompt(args)

        assert result == 0
        # Verify execution_dir was validated and passed to ask_llm
        call_kwargs = mock_ask_llm.call_args[1]
        assert "execution_dir" in call_kwargs
        assert call_kwargs["execution_dir"] == str(execution_dir)
        captured = capsys.readouterr()
        assert "Response with explicit execution_dir." in captured.out

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_explicit_execution_dir_relative(
        self,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test explicit relative execution_dir should be resolved to CWD."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_ask_llm.return_value = "Response with relative execution_dir."

        # Create a valid temporary directory structure
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        rel_dir = base_dir / "relative"
        rel_dir.mkdir()

        # Change to base directory so relative path works
        monkeypatch.chdir(base_dir)

        args = argparse.Namespace(
            prompt="Test prompt",
            execution_dir="relative",  # Relative path
        )

        result = execute_prompt(args)

        assert result == 0
        # Verify execution_dir was resolved to absolute path
        call_kwargs = mock_ask_llm.call_args[1]
        assert "execution_dir" in call_kwargs
        assert call_kwargs["execution_dir"] == str(rel_dir)
        captured = capsys.readouterr()
        assert "Response with relative execution_dir." in captured.out

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    def test_invalid_execution_dir_returns_error(
        self,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test invalid execution_dir should return error code 1."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}

        args = argparse.Namespace(
            prompt="Test prompt",
            execution_dir="/nonexistent/invalid/path",
        )

        result = execute_prompt(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "execution directory" in captured.err.lower()

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_execution_dir_with_all_other_args(
        self,
        mock_ask_llm: Mock,
        mock_prepare_env: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test execution_dir works with all other args (no conflicts)."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_ask_llm.return_value = "Response with all args."

        # Create valid directories
        execution_dir = tmp_path / "exec_dir"
        execution_dir.mkdir()
        project_dir = tmp_path / "project_dir"
        project_dir.mkdir()

        args = argparse.Namespace(
            prompt="Test prompt",
            execution_dir=str(execution_dir),
            project_dir=str(project_dir),
            timeout=60,
            llm_method="claude_code_api",
            verbosity="just-text",
            session_id="test-session-123",
            mcp_config=None,
        )

        result = execute_prompt(args)

        assert result == 0
        # Verify all arguments were passed correctly
        call_kwargs = mock_ask_llm.call_args[1]
        assert call_kwargs["execution_dir"] == str(execution_dir)
        assert call_kwargs["project_dir"] == str(project_dir)
        assert call_kwargs["timeout"] == 60
        assert call_kwargs["session_id"] == "test-session-123"
        captured = capsys.readouterr()
        assert "Response with all args." in captured.out
