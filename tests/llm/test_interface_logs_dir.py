from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.llm.interface import prompt_llm, prompt_llm_stream
from tests.llm.test_interface import PROJECT_DIR


class TestPromptLLMLogsDirDerivation:
    """Tests for logs_dir derivation from env_vars in prompt_llm."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_logs_dir_derived_from_env_vars_project_dir(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """When env_vars has MCP_CODER_PROJECT_DIR, logs_dir is derived and passed."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with logs_dir",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }
        test_env_vars = {"MCP_CODER_PROJECT_DIR": "/home/user/mcp-coder"}

        result = prompt_llm(
            "Test question", env_vars=test_env_vars, project_dir=PROJECT_DIR
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=str(Path("/home/user/mcp-coder") / "logs"),
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response with logs_dir"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_logs_dir_none_when_env_vars_missing_project_dir(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """When env_vars lacks MCP_CODER_PROJECT_DIR, logs_dir=None."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response without project dir",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }
        test_env_vars = {"OTHER_VAR": "some_value"}

        result = prompt_llm(
            "Test question", env_vars=test_env_vars, project_dir=PROJECT_DIR
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response without project dir"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_logs_dir_none_when_env_vars_is_none(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """When env_vars is None, logs_dir=None (backward compat)."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with no env vars",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm("Test question", env_vars=None, project_dir=PROJECT_DIR)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response with no env vars"


class TestPromptLLMStreamLogsDirDerivation:
    """Tests for logs_dir derivation from env_vars in prompt_llm_stream."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_logs_dir_derived_from_env_vars_project_dir(
        self, mock_stream: MagicMock
    ) -> None:
        """When env_vars has MCP_CODER_PROJECT_DIR, logs_dir is derived and passed."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])
        test_env_vars = {"MCP_CODER_PROJECT_DIR": "/home/user/mcp-coder"}

        list(
            prompt_llm_stream(
                "Test question", env_vars=test_env_vars, project_dir=PROJECT_DIR
            )
        )

        mock_stream.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=str(Path("/home/user/mcp-coder") / "logs"),
            append_system_prompt=None,
            system_prompt_replace=None,
        )

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_logs_dir_none_when_env_vars_missing_project_dir(
        self, mock_stream: MagicMock
    ) -> None:
        """When env_vars lacks MCP_CODER_PROJECT_DIR, logs_dir=None."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])
        test_env_vars = {"OTHER_VAR": "some_value"}

        list(
            prompt_llm_stream(
                "Test question", env_vars=test_env_vars, project_dir=PROJECT_DIR
            )
        )

        mock_stream.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_logs_dir_none_when_env_vars_is_none(self, mock_stream: MagicMock) -> None:
        """When env_vars is None, logs_dir=None (backward compat)."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        list(prompt_llm_stream("Test question", env_vars=None, project_dir=PROJECT_DIR))

        mock_stream.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
