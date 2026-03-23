"""Tests for mcp_coder.llm.providers.langchain.__init__."""

import uuid
from unittest.mock import MagicMock, patch

import pytest


class TestLoadLangchainConfig:
    """Tests for _load_langchain_config function."""

    def test_returns_expected_keys(self) -> None:
        """_load_langchain_config returns a dict with all expected keys."""
        with patch(
            "mcp_coder.llm.providers.langchain.get_config_values",
            return_value={
                ("llm", "default_provider"): "langchain",
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
            "default_provider",
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
                ("llm", "default_provider"): "langchain",
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
                ("llm", "default_provider"): "langchain",
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
    """Tests for ask_langchain function."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def _mock_chat_model(self, text: str = "Hello!") -> MagicMock:
        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = text
        mock_ai_msg.model_dump.return_value = {"type": "ai", "content": text}
        mock_model.invoke.return_value = mock_ai_msg
        return mock_model

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
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=self._mock_chat_model("Hello!"),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("Hi")
        assert result["text"] == "Hello!"
        assert result["provider"] == "langchain"
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
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=self._mock_chat_model("ok"),
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
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=self._mock_chat_model("ok"),
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
        """After a call, history is stored in messages_from_dict format."""
        store_mock = MagicMock()
        # Provide prior history in the new serialized format
        prior_history = [
            {"type": "human", "data": {"content": "prev"}},
        ]
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=prior_history,
            ),
            patch(
                "mcp_coder.llm.providers.langchain.store_langchain_history",
                store_mock,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=self._mock_chat_model("answer"),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("new question", session_id="sid")
        stored_messages = store_mock.call_args[0][1]  # second positional arg
        # All entries should use {"type": ..., "data": {...}} format
        types = [m["type"] for m in stored_messages]
        assert types == ["human", "human", "ai"]
        contents = [m["data"]["content"] for m in stored_messages]
        assert contents == ["prev", "new question", "answer"]


class TestAskTextModelNotFound:
    """Tests for model-not-found error handling in _ask_text."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "bad-model",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_404_error_raises_value_error_with_model_hint(self) -> None:
        """404 from model invoke raises ValueError with model name."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception(
            "Error code: 404 - The model 'bad-model' does not exist"
        )
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=mock_model,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._get_model_suggestions",
                return_value="\n\nAvailable models:\n  - gpt-4o",
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError) as exc_info:
                ask_langchain("question")
        assert "bad-model" in str(exc_info.value)
        assert "gpt-4o" in str(exc_info.value)

    def test_not_found_error_raised_even_when_suggestions_fail(self) -> None:
        """404 still raises ValueError even if model listing fails."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("404 not_found_error")
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=mock_model,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._get_model_suggestions",
                side_effect=Exception("network error"),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError, match="not found"):
                ask_langchain("question")

    def test_non_404_exception_is_reraised_unchanged(self) -> None:
        """Non-404 exceptions propagate as-is without wrapping."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = RuntimeError("network timeout")
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=mock_model,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(RuntimeError, match="network timeout"):
                ask_langchain("question")


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
            model="gpt-4o", api_key="k", endpoint=None, api_version=None, timeout=30
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
        mock_create.assert_called_once_with(
            model="gemini-2.0-flash", api_key="k", timeout=30
        )

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
            model="claude-sonnet-4-20250514", api_key="k", timeout=30
        )

    def test_raises_on_unknown_backend(self) -> None:
        """Unknown backend raises ValueError."""
        from mcp_coder.llm.providers.langchain import _create_chat_model

        with pytest.raises(ValueError, match="unknown_llm"):
            _create_chat_model({"backend": "unknown_llm", "model": "x"})


# ---------------------------------------------------------------------------
# Fake exception classes for testing error tuple patching
# ---------------------------------------------------------------------------


class _FakeAuthError(Exception):
    """Fake auth error for testing exception tuple patching."""


class _FakeClientError(Exception):
    """Fake Google ClientError for testing."""

    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


_MOD = "mcp_coder.llm.providers.langchain"


# ---------------------------------------------------------------------------
# _ask_text connection/auth error tests
# ---------------------------------------------------------------------------


class TestAskTextConnectionError:
    """_ask_text wraps connection errors as LLMConnectionError."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_connection_error_raises_llm_connection_error(self) -> None:
        """OSError from chat_model.invoke() raises LLMConnectionError."""
        from mcp_coder.llm.providers.langchain._exceptions import LLMConnectionError

        mock_model = MagicMock()
        mock_model.invoke.side_effect = OSError("Connection reset by peer")
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(LLMConnectionError):
                ask_langchain("question")

    def test_connection_error_message_contains_provider_hint(self) -> None:
        """LLMConnectionError message contains provider name and env var hint."""
        from mcp_coder.llm.providers.langchain._exceptions import LLMConnectionError

        mock_model = MagicMock()
        mock_model.invoke.side_effect = OSError("Connection reset")
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config("openai"),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(LLMConnectionError, match="OPENAI_API_KEY") as exc_info:
                ask_langchain("question")
        assert "OpenAI" in str(exc_info.value)


class TestAskTextAuthError:
    """_ask_text wraps auth errors as LLMAuthError."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_auth_error_raises_llm_auth_error(self) -> None:
        """Auth error from chat_model.invoke() raises LLMAuthError."""
        from mcp_coder.llm.providers.langchain._exceptions import LLMAuthError

        mock_model = MagicMock()
        mock_model.invoke.side_effect = _FakeAuthError("invalid key")
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config("openai"),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD}.OPENAI_AUTH_ERRORS", (_FakeAuthError,)),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(LLMAuthError):
                ask_langchain("question")

    def test_auth_error_message_contains_provider_hint(self) -> None:
        """LLMAuthError message contains provider name and env var hint."""
        from mcp_coder.llm.providers.langchain._exceptions import LLMAuthError

        mock_model = MagicMock()
        mock_model.invoke.side_effect = _FakeAuthError("invalid key")
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config("openai"),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD}.OPENAI_AUTH_ERRORS", (_FakeAuthError,)),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(LLMAuthError, match="OPENAI_API_KEY") as exc_info:
                ask_langchain("question")
        assert "OpenAI" in str(exc_info.value)


# ---------------------------------------------------------------------------
# _ask_agent connection/auth error tests
# ---------------------------------------------------------------------------


class TestAskAgentConnectionError:
    """_ask_agent wraps connection errors as LLMConnectionError."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_connection_error_raises_llm_connection_error(self) -> None:
        """OSError from asyncio.run(run_agent(...)) raises LLMConnectionError."""
        from mcp_coder.llm.providers.langchain._exceptions import LLMConnectionError

        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD}.agent._check_agent_dependencies"),
            patch(f"{_MOD}.asyncio.run", side_effect=OSError("Connection refused")),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(LLMConnectionError):
                ask_langchain("question", mcp_config="/tmp/mcp.json")

    def test_non_connection_error_propagates(self) -> None:
        """Non-connection errors propagate unchanged from agent path."""
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD}.asyncio.run",
                side_effect=RuntimeError("unexpected agent error"),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(RuntimeError, match="unexpected agent error"):
                ask_langchain("question", mcp_config="/tmp/mcp.json")


class TestAskAgentAuthError:
    """_ask_agent wraps auth errors as LLMAuthError."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_auth_error_raises_llm_auth_error(self) -> None:
        """Auth error from agent run raises LLMAuthError."""
        from mcp_coder.llm.providers.langchain._exceptions import LLMAuthError

        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config("openai"),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD}.asyncio.run",
                side_effect=_FakeAuthError("invalid key"),
            ),
            patch(f"{_MOD}.OPENAI_AUTH_ERRORS", (_FakeAuthError,)),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(LLMAuthError):
                ask_langchain("question", mcp_config="/tmp/mcp.json")


# ---------------------------------------------------------------------------
# ensure_truststore integration tests
# ---------------------------------------------------------------------------


class TestEnsureTruststoreCalled:
    """Both _ask_text and _ask_agent call ensure_truststore."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def _mock_chat_model(self, text: str = "Hello!") -> MagicMock:
        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = text
        mock_ai_msg.model_dump.return_value = {"type": "ai", "content": text}
        mock_model.invoke.return_value = mock_ai_msg
        return mock_model

    def test_ask_text_calls_ensure_truststore(self) -> None:
        """_ask_text calls ensure_truststore before model creation."""
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(
                f"{_MOD}._create_chat_model",
                return_value=self._mock_chat_model(),
            ),
            patch(f"{_MOD}.ensure_truststore") as mock_ts,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("question")
        mock_ts.assert_called_once()

    def test_ask_agent_calls_ensure_truststore(self) -> None:
        """_ask_agent calls ensure_truststore before model creation."""
        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=MagicMock()),
            patch(f"{_MOD}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD}.asyncio.run",
                return_value=(
                    "response",
                    [],
                    {"agent_steps": 1, "total_tool_calls": 0},
                ),
            ),
            patch(f"{_MOD}.ensure_truststore") as mock_ts,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("question", mcp_config="/tmp/mcp.json")
        mock_ts.assert_called_once()
