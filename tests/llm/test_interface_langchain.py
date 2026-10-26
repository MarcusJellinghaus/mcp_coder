from unittest.mock import patch

import pytest

from tests.llm.test_interface import PROJECT_DIR


class TestPromptLlmLangchainRouting:
    """Test that prompt_llm correctly routes to the langchain provider."""

    def _make_langchain_response(
        self, text: str = "langchain reply"
    ) -> dict[str, object]:
        from datetime import datetime

        return {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "session_id": "uuid-langchain-session",
            "provider": "langchain",
            "raw_response": {},
        }

    def _make_claude_response(self, text: str = "claude reply") -> dict[str, object]:
        from datetime import datetime

        return {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "session_id": "uuid-claude-session",
            "provider": "claude",
            "raw_response": {},
        }

    def test_routes_to_langchain_provider(self) -> None:
        """prompt_llm with provider='langchain' calls ask_langchain."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", provider="langchain", project_dir=PROJECT_DIR)

        mock_ask.assert_called_once()
        assert result["provider"] == "langchain"
        assert result["text"] == "langchain reply"

    def test_passes_question_session_timeout(self) -> None:
        """prompt_llm passes question, session_id, timeout to ask_langchain."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            prompt_llm(
                "test question",
                provider="langchain",
                session_id="my-sid",
                timeout=60,
                project_dir=PROJECT_DIR,
            )

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        args, kwargs = call_kwargs
        all_args = {
            **dict(zip(["question", "session_id", "timeout"], args, strict=False)),
            **kwargs,
        }
        assert all_args.get("session_id") == "my-sid"
        assert all_args.get("timeout") == 60

    def test_unsupported_provider_error_mentions_langchain(self) -> None:
        """The ValueError for unsupported providers lists 'langchain' as supported."""
        from mcp_coder.llm.interface import prompt_llm

        with pytest.raises(ValueError) as exc_info:
            prompt_llm("Hello", provider="unsupported_xyz", project_dir=PROJECT_DIR)
        assert "langchain" in str(exc_info.value)

    def test_unsupported_provider_error_mentions_copilot(self) -> None:
        """The ValueError for unsupported providers lists 'copilot' as supported."""
        from mcp_coder.llm.interface import prompt_llm

        with pytest.raises(ValueError) as exc_info:
            prompt_llm("Hello", provider="unsupported_xyz", project_dir=PROJECT_DIR)
        assert "copilot" in str(exc_info.value)

    def test_explicit_provider_beats_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicitly passed provider wins over MCP_CODER_LLM_PROVIDER."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        expected = self._make_langchain_response()
        with (
            patch(
                "mcp_coder.llm.providers.langchain.ask_langchain",
                return_value=expected,
            ) as mock_langchain,
            patch(
                "mcp_coder.llm.interface.ask_claude_code_cli",
                return_value=self._make_claude_response(),
            ) as mock_claude,
        ):
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", provider="claude", project_dir=PROJECT_DIR)

        mock_langchain.assert_not_called()
        mock_claude.assert_called_once()
        assert result["provider"] == "claude"

    def test_env_var_used_when_provider_omitted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_PROVIDER applies when no provider argument is given."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_langchain:
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", project_dir=PROJECT_DIR)

        mock_langchain.assert_called_once()
        assert result["provider"] == "langchain"

    def test_defaults_to_claude_when_provider_and_env_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With no provider argument and no env var, claude is used."""
        monkeypatch.delenv("MCP_CODER_LLM_PROVIDER", raising=False)
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            return_value=self._make_claude_response(),
        ) as mock_claude:
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", project_dir=PROJECT_DIR)

        mock_claude.assert_called_once()
        assert result["provider"] == "claude"

    def test_unsupported_provider_still_raises_after_resolution(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicit unsupported provider raises even with a valid env var set."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        from mcp_coder.llm.interface import prompt_llm

        with pytest.raises(ValueError, match="Unsupported provider: unsupported_xyz"):
            prompt_llm("Hello", provider="unsupported_xyz", project_dir=PROJECT_DIR)

    def test_passes_mcp_config_to_langchain(self) -> None:
        """mcp_config parameter is forwarded to ask_langchain()."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            prompt_llm(
                "Hello",
                provider="langchain",
                mcp_config="/path/to/mcp.json",
                project_dir=PROJECT_DIR,
            )

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("mcp_config") == "/path/to/mcp.json"

    def test_passes_env_vars_to_langchain(self) -> None:
        """env_vars parameter is forwarded to ask_langchain()."""
        expected = self._make_langchain_response()
        test_env = {"KEY": "value"}
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            prompt_llm(
                "Hello",
                provider="langchain",
                env_vars=test_env,
                project_dir=PROJECT_DIR,
            )

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("env_vars") == {"KEY": "value"}

    def test_langchain_without_mcp_params_still_works(self) -> None:
        """Calling with provider=langchain and no MCP params works (backward compat)."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", provider="langchain", project_dir=PROJECT_DIR)

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("mcp_config") is None
        assert kwargs.get("env_vars") is None
        assert result["text"] == "langchain reply"

    def test_prompt_llm_returns_full_response_for_langchain(self) -> None:
        """prompt_llm with provider='langchain' returns full dict response."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ):
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", provider="langchain", project_dir=PROJECT_DIR)
        assert result["text"] == "langchain reply"
        assert result["provider"] == "langchain"
