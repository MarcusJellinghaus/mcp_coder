"""Tests for mcp_coder.llm.providers.langchain.__init__."""

import uuid
from unittest.mock import MagicMock, patch

import pytest


class TestLoadLangchainConfig:
    def test_returns_expected_keys(self) -> None:
        """_load_langchain_config returns a dict with all expected keys."""
        with patch(
            "mcp_coder.llm.providers.langchain.get_config_values",
            return_value={
                ("llm", "provider"): "langchain",
                ("llm.langchain", "backend"): "openai",
                ("llm.langchain", "model"): "gpt-4o",
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "endpoint"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            from mcp_coder.llm.providers.langchain import _load_langchain_config

            cfg = _load_langchain_config()
        assert set(cfg.keys()) == {
            "provider",
            "backend",
            "model",
            "api_key",
            "endpoint",
            "api_version",
        }

    def test_env_var_overrides_config_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_LANGCHAIN_* env vars override config.toml values."""
        monkeypatch.setenv("MCP_CODER_LLM_LANGCHAIN_BACKEND", "gemini")
        monkeypatch.setenv("MCP_CODER_LLM_LANGCHAIN_MODEL", "gemini-2.0-flash")
        with patch(
            "mcp_coder.llm.providers.langchain.get_config_values",
            return_value={
                ("llm", "provider"): "langchain",
                ("llm.langchain", "backend"): "openai",
                ("llm.langchain", "model"): "gpt-4o",
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "endpoint"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            from mcp_coder.llm.providers.langchain import _load_langchain_config

            cfg = _load_langchain_config()
        assert cfg["backend"] == "gemini"
        assert cfg["model"] == "gemini-2.0-flash"

    def test_env_var_does_not_override_when_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty env vars do not override config.toml values."""
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_BACKEND", raising=False)
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_MODEL", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.get_config_values",
            return_value={
                ("llm", "provider"): "langchain",
                ("llm.langchain", "backend"): "openai",
                ("llm.langchain", "model"): "gpt-4o",
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "endpoint"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            from mcp_coder.llm.providers.langchain import _load_langchain_config

            cfg = _load_langchain_config()
        assert cfg["backend"] == "openai"
        assert cfg["model"] == "gpt-4o"


class TestAskLangchain:
    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_returns_llm_response_dict(self) -> None:
        """ask_langchain returns a complete LLMResponseDict."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ask_openai",
                return_value=("Hello!", {"content": "Hello!"}),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("Hi")
        assert result["text"] == "Hello!"
        assert result["provider"] == "langchain"
        assert result["method"] == "api"
        assert result["session_id"] is not None

    def test_generates_session_id_when_none_given(self) -> None:
        """A UUID session_id is generated when none is provided."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ask_openai",
                return_value=("ok", {}),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("question")
        # Must be a valid UUID
        uuid.UUID(str(result["session_id"]))

    def test_preserves_provided_session_id(self) -> None:
        """When session_id is passed, it is preserved in the response."""
        sid = "my-session-123"
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ask_openai",
                return_value=("ok", {}),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("question", session_id=sid)
        assert result["session_id"] == sid

    def test_raises_value_error_for_unknown_backend(self) -> None:
        """Unsupported backend raises ValueError with a clear message."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value={**self._make_config(), "backend": "unknown_llm"},
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError, match="unknown_llm"):
                ask_langchain("question")

    def test_raises_value_error_when_backend_not_configured(self) -> None:
        """Missing backend config raises ValueError."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value={**self._make_config(), "backend": None},
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError, match="backend"):
                ask_langchain("question")

    def test_history_is_updated_and_stored(self) -> None:
        """After a call, both human and AI messages are appended to history."""
        store_mock = MagicMock()
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[{"role": "human", "content": "prev"}],
            ),
            patch(
                "mcp_coder.llm.providers.langchain.store_langchain_history",
                store_mock,
            ),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ask_openai",
                return_value=("answer", {}),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("new question", session_id="sid")
        stored_messages = store_mock.call_args[0][1]  # second positional arg
        assert {"role": "human", "content": "prev"} in stored_messages
        assert {"role": "human", "content": "new question"} in stored_messages
        assert {"role": "ai", "content": "answer"} in stored_messages


class TestCreateChatModel:
    """Tests for _create_chat_model() dispatcher."""

    def test_dispatches_to_openai_backend(self) -> None:
        """Config with backend=openai calls create_openai_model."""
        mock_model = MagicMock()
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.create_openai_model",
            return_value=mock_model,
        ) as mock_create:
            from mcp_coder.llm.providers.langchain import _create_chat_model

            result = _create_chat_model(
                {"backend": "openai", "model": "gpt-4o", "api_key": "k"}
            )
        assert result is mock_model
        mock_create.assert_called_once_with(
            model="gpt-4o", api_key="k", endpoint=None, api_version=None
        )

    def test_dispatches_to_gemini_backend(self) -> None:
        """Config with backend=gemini calls create_gemini_model."""
        mock_model = MagicMock()
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.create_gemini_model",
            return_value=mock_model,
        ) as mock_create:
            from mcp_coder.llm.providers.langchain import _create_chat_model

            result = _create_chat_model(
                {"backend": "gemini", "model": "gemini-2.0-flash", "api_key": "k"}
            )
        assert result is mock_model
        mock_create.assert_called_once_with(model="gemini-2.0-flash", api_key="k")

    def test_dispatches_to_anthropic_backend(self) -> None:
        """Config with backend=anthropic calls create_anthropic_model."""
        mock_model = MagicMock()
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic_backend.create_anthropic_model",
            return_value=mock_model,
        ) as mock_create:
            from mcp_coder.llm.providers.langchain import _create_chat_model

            result = _create_chat_model(
                {
                    "backend": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "api_key": "k",
                }
            )
        assert result is mock_model
        mock_create.assert_called_once_with(
            model="claude-sonnet-4-20250514", api_key="k"
        )

    def test_raises_on_unknown_backend(self) -> None:
        """Unknown backend raises ValueError."""
        from mcp_coder.llm.providers.langchain import _create_chat_model

        with pytest.raises(ValueError, match="unknown_llm"):
            _create_chat_model({"backend": "unknown_llm", "model": "x"})


class TestCheckAgentDependencies:
    """Tests for _check_agent_dependencies()."""

    def test_passes_when_both_installed(self) -> None:
        """No error when both packages importable."""
        from mcp_coder.llm.providers.langchain.agent import (
            _check_agent_dependencies,
        )

        # Both are mocked in conftest, so this should not raise
        _check_agent_dependencies()

    def test_raises_clear_error_when_mcp_adapters_missing(self) -> None:
        """ImportError with install instructions for langchain-mcp-adapters."""
        import importlib
        import sys

        from mcp_coder.llm.providers.langchain import agent as agent_module

        saved = sys.modules.get("langchain_mcp_adapters")
        sys.modules["langchain_mcp_adapters"] = None  # type: ignore[assignment]
        try:
            importlib.reload(agent_module)
            with pytest.raises(ImportError, match="langchain-mcp-adapters"):
                agent_module._check_agent_dependencies()
        finally:
            if saved is not None:
                sys.modules["langchain_mcp_adapters"] = saved
            else:
                sys.modules.pop("langchain_mcp_adapters", None)
            importlib.reload(agent_module)

    def test_raises_clear_error_when_langgraph_missing(self) -> None:
        """ImportError with install instructions for langgraph."""
        import importlib
        import sys

        from mcp_coder.llm.providers.langchain import agent as agent_module

        saved = sys.modules.get("langgraph")
        sys.modules["langgraph"] = None  # type: ignore[assignment]
        try:
            importlib.reload(agent_module)
            with pytest.raises(ImportError, match="langgraph"):
                agent_module._check_agent_dependencies()
        finally:
            if saved is not None:
                sys.modules["langgraph"] = saved
            else:
                sys.modules.pop("langgraph", None)
            importlib.reload(agent_module)
