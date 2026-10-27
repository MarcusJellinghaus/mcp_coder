"""Tests for the high-level LLM interface."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import prompt_llm, prompt_llm_stream

# prompt_llm normalises project_dir with Path(), so the expected cwd is the
# normalised form of whatever the test passes in.
PROJECT_DIR = str(Path("/test/project"))


class TestPromptLLMProjectDirRouting:
    """Tests for project_dir parameter routing in prompt_llm."""

    def test_project_dir_is_required(self) -> None:
        """prompt_llm without project_dir raises TypeError (no silent cwd fallback)."""
        with pytest.raises(TypeError):
            prompt_llm("hi")  # type: ignore[call-arg]  # pylint: disable=missing-kwoa

    def test_prompt_llm_stream_project_dir_is_required(self) -> None:
        """prompt_llm_stream without project_dir raises TypeError."""
        with pytest.raises(TypeError):
            list(prompt_llm_stream("hi"))  # type: ignore[call-arg]  # pylint: disable=missing-kwoa

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_project_dir_passed_to_provider(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """project_dir should be passed as cwd to provider."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with project_dir",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question",
            project_dir=str(Path("/custom/project/dir")),
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/custom/project/dir")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response with project_dir"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_project_dir_accepts_path_object(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """project_dir accepts a Path and is normalised to a str cwd."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with absolute path",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question",
            project_dir=Path("/home/user/workspace"),
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/home/user/workspace")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response with absolute path"


class TestIntegration:
    """Integration tests for the full routing chain."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_full_routing_chain(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """Test the full routing chain from prompt_llm to ask_claude_code_cli."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Full chain response",
            "session_id": "chain-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Integration test question",
            provider="claude",
            timeout=25,
            project_dir=PROJECT_DIR,
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Integration test question",
            session_id=None,
            timeout=25,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Full chain response"

    def test_parameter_validation_propagation(self) -> None:
        """Test that parameter validation errors propagate correctly."""
        # Test invalid provider
        with pytest.raises(ValueError, match="Unsupported provider"):
            prompt_llm("Test", provider="invalid", project_dir=PROJECT_DIR)

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_full_routing_chain_with_session_id(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test the full routing chain with session_id parameter."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Full chain response with session",
            "session_id": "integration-session-789",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Integration test with session",
            provider="claude",
            session_id="integration-session-789",
            timeout=25,
            project_dir=PROJECT_DIR,
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Integration test with session",
            session_id="integration-session-789",
            timeout=25,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Full chain response with session"


# Real integration tests for LLM interface are removed
# These are redundant with the critical path tests in test_claude_integration.py
# The interface routing and functionality is covered by the streamlined integration tests


class TestPromptLLMProjectDir:
    """Tests for project_dir parameter in prompt_llm."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_project_dir_with_cli(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """project_dir should be passed to CLI provider."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "CLI response with project_dir",
            "session_id": "cli-exec-123",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm(
            "Test question",
            project_dir=str(Path("/custom/project/path")),
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/custom/project/path")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "CLI response with project_dir"


class TestUnsupportedProviderListsAllProviders:
    """Test that unsupported provider error message lists all providers."""

    def test_unsupported_provider_error_lists_all_providers(self) -> None:
        """Error message includes 'copilot', 'claude', 'langchain'."""
        with pytest.raises(ValueError) as exc_info:
            prompt_llm("Test", provider="invalid", project_dir=PROJECT_DIR)

        error_msg = str(exc_info.value)
        assert "copilot" in error_msg
        assert "claude" in error_msg
        assert "langchain" in error_msg

    def test_unsupported_provider_stream_error_lists_all_providers(self) -> None:
        """Stream error message includes 'copilot', 'claude', 'langchain'."""
        with pytest.raises(ValueError) as exc_info:
            list(prompt_llm_stream("Test", provider="invalid", project_dir=PROJECT_DIR))

        error_msg = str(exc_info.value)
        assert "copilot" in error_msg
        assert "claude" in error_msg
        assert "langchain" in error_msg
