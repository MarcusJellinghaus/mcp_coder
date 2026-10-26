"""Tests for the high-level LLM interface."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm, prompt_llm_stream
from mcp_coder.utils.subprocess_runner import TimeoutExpired

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


class TestPromptLlmCopilotRouting:
    """Tests for copilot provider routing in prompt_llm and prompt_llm_stream."""

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_prompt_llm_routes_to_copilot(self, mock_ask_copilot: MagicMock) -> None:
        """prompt_llm routes to ask_copilot_cli for copilot provider."""
        mock_ask_copilot.return_value = {
            "text": "Copilot response",
            "session_id": "copilot-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "copilot",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question", provider="copilot", timeout=30, project_dir=PROJECT_DIR
        )

        mock_ask_copilot.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            logs_dir=None,
            branch_name=None,
            system_prompt=None,
        )
        assert result["text"] == "Copilot response"
        assert result["provider"] == "copilot"

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli_stream")
    def test_prompt_llm_stream_routes_to_copilot(self, mock_stream: MagicMock) -> None:
        """prompt_llm_stream routes to ask_copilot_cli_stream for copilot provider."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(
            prompt_llm_stream("Hello", provider="copilot", project_dir=PROJECT_DIR)
        )

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            logs_dir=None,
            branch_name=None,
            system_prompt=None,
        )
        assert len(events) == 2
        assert events[0]["type"] == "text_delta"


class TestCopilotSystemPromptHandling:
    """Tests for system prompt handling in copilot provider."""

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_copilot_system_prompt_passed_on_new_session(
        self,
        mock_ask_copilot: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """No session_id → system_prompt forwarded to copilot."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "system prompt content",
            "project prompt content",
            mock_config,
        )
        mock_ask_copilot.return_value = {
            "text": "Copilot reply",
            "session_id": "new-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "copilot",
            "raw_response": {},
        }

        prompt_llm(
            "Test question",
            provider="copilot",
            project_dir="/my/project",
            inject_prompts=True,
        )

        call_kwargs = mock_ask_copilot.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs["system_prompt"] == "system prompt content"

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_copilot_system_prompt_skipped_on_resume(
        self,
        mock_ask_copilot: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """session_id set → system_prompt=None for copilot."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "system prompt content",
            "project prompt content",
            mock_config,
        )
        mock_ask_copilot.return_value = {
            "text": "Copilot reply",
            "session_id": "existing-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "copilot",
            "raw_response": {},
        }

        prompt_llm(
            "Test question",
            provider="copilot",
            session_id="existing-session",
            project_dir="/my/project",
            inject_prompts=True,
        )

        call_kwargs = mock_ask_copilot.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs["system_prompt"] is None

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_copilot_project_prompt_always_skipped(
        self,
        mock_ask_copilot: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """project_prompt is never forwarded to copilot (reads CLAUDE.md natively)."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "system prompt",
            "project prompt that should NOT appear",
            mock_config,
        )
        mock_ask_copilot.return_value = {
            "text": "Copilot reply",
            "session_id": "session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "copilot",
            "raw_response": {},
        }

        prompt_llm(
            "Test question",
            provider="copilot",
            project_dir="/my/project",
            inject_prompts=True,
        )

        call_kwargs = mock_ask_copilot.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        # system_prompt should be present but project_prompt should NOT
        assert kwargs["system_prompt"] == "system prompt"
        # ask_copilot_cli has no project_prompt parameter
        assert "project_prompt" not in kwargs


class TestCopilotTimeoutHandling:
    """Tests for copilot timeout error normalization."""

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_copilot_timeout_raises_llm_timeout_error(
        self, mock_ask_copilot: MagicMock
    ) -> None:
        """TimeoutExpired from copilot is normalized to LLMTimeoutError."""
        mock_ask_copilot.side_effect = TimeoutExpired(cmd="copilot", timeout=30)

        with pytest.raises(LLMTimeoutError) as exc_info:
            prompt_llm(
                "Test question", provider="copilot", timeout=30, project_dir=PROJECT_DIR
            )

        assert isinstance(exc_info.value, TimeoutError)
        assert "30s" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, TimeoutExpired)


class TestCopilotProviderValidation:
    """Tests that copilot is accepted as a valid provider."""

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_prompt_llm_accepts_copilot_provider(
        self, mock_ask_copilot: MagicMock
    ) -> None:
        """No ValueError for provider='copilot'."""
        mock_ask_copilot.return_value = {
            "text": "ok",
            "session_id": "s",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "copilot",
            "raw_response": {},
        }

        # Should not raise
        result = prompt_llm("Test", provider="copilot", project_dir=PROJECT_DIR)
        assert result["text"] == "ok"

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli_stream")
    def test_prompt_llm_stream_accepts_copilot_provider(
        self, mock_stream: MagicMock
    ) -> None:
        """No ValueError for provider='copilot' in stream mode."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        # Should not raise
        events = list(
            prompt_llm_stream("Test", provider="copilot", project_dir=PROJECT_DIR)
        )
        assert len(events) == 1


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
