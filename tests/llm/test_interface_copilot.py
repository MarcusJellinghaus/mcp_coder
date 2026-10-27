from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm, prompt_llm_stream
from mcp_coder.utils.subprocess_runner import TimeoutExpired
from tests.llm.test_interface import PROJECT_DIR


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
