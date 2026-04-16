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
        """MCP_CODER_LLM_LANGCHAIN_* env vars override config.toml values.

        Env var overrides are now handled by get_config_values() via the schema,
        so the mock returns values as if env vars were already resolved.
        """
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_BACKEND", raising=False)
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_MODEL", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.get_config_values",
            return_value={
                ("llm", "default_provider"): "langchain",
                ("llm.langchain", "backend"): "gemini",
                ("llm.langchain", "model"): "gemini-2.0-flash",
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
# _extract_usage / _sum_usage tests
# ---------------------------------------------------------------------------


class TestExtractUsage:
    """_extract_usage maps LangChain usage_metadata onto UsageInfo."""

    def test_extract_usage_full_metadata(self) -> None:
        """AIMessage with full usage_metadata yields all 4 UsageInfo fields."""
        from mcp_coder.llm.providers.langchain._usage import _extract_usage

        ai_msg = MagicMock()
        ai_msg.usage_metadata = {
            "input_tokens": 1200,
            "output_tokens": 800,
            "total_tokens": 2000,
            "input_token_details": {
                "cache_read": 540,
                "cache_creation": 100,
            },
        }
        usage = _extract_usage(ai_msg)
        assert usage == {
            "input_tokens": 1200,
            "output_tokens": 800,
            "cache_read_input_tokens": 540,
            "cache_creation_input_tokens": 100,
        }

    def test_extract_usage_no_metadata(self) -> None:
        """Missing/empty usage_metadata returns empty dict in all cases."""
        from mcp_coder.llm.providers.langchain._usage import _extract_usage

        # Case (a): attribute absent on message
        class _NoAttr:
            pass

        assert _extract_usage(_NoAttr()) == {}

        # Case (b): usage_metadata is None
        msg_none = MagicMock(spec=[])  # no default usage_metadata attr
        msg_none.usage_metadata = None
        assert _extract_usage(msg_none) == {}

        # Case (c): usage_metadata is empty dict
        msg_empty = MagicMock(spec=[])
        msg_empty.usage_metadata = {}
        assert _extract_usage(msg_empty) == {}

    def test_extract_usage_no_cache_details(self) -> None:
        """usage_metadata with tokens but no input_token_details yields 2 fields."""
        from mcp_coder.llm.providers.langchain._usage import _extract_usage

        ai_msg = MagicMock()
        ai_msg.usage_metadata = {
            "input_tokens": 500,
            "output_tokens": 250,
            "total_tokens": 750,
        }
        usage = _extract_usage(ai_msg)
        assert usage == {"input_tokens": 500, "output_tokens": 250}


class TestSumUsage:
    """_sum_usage adds two UsageInfo dicts field-by-field, always 4 keys."""

    def test_sum_usage_basic(self) -> None:
        """Sum two dicts with all fields present."""
        from mcp_coder.llm.providers.langchain._usage import _sum_usage
        from mcp_coder.llm.types import UsageInfo

        a: UsageInfo = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 10,
            "cache_creation_input_tokens": 5,
        }
        b: UsageInfo = {
            "input_tokens": 200,
            "output_tokens": 75,
            "cache_read_input_tokens": 20,
            "cache_creation_input_tokens": 15,
        }
        assert _sum_usage(a, b) == {
            "input_tokens": 300,
            "output_tokens": 125,
            "cache_read_input_tokens": 30,
            "cache_creation_input_tokens": 20,
        }

    def test_sum_usage_partial_keys(self) -> None:
        """One dict has cache, other doesn't — all 4 keys present in result."""
        from mcp_coder.llm.providers.langchain._usage import _sum_usage
        from mcp_coder.llm.types import UsageInfo

        a: UsageInfo = {"input_tokens": 100, "output_tokens": 50}
        b: UsageInfo = {
            "input_tokens": 200,
            "output_tokens": 100,
            "cache_read_input_tokens": 30,
            "cache_creation_input_tokens": 5,
        }
        assert _sum_usage(a, b) == {
            "input_tokens": 300,
            "output_tokens": 150,
            "cache_read_input_tokens": 30,
            "cache_creation_input_tokens": 5,
        }


class TestAskTextIncludesUsage:
    """_ask_text populates raw_response['usage'] via _extract_usage."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_ask_text_includes_usage(self) -> None:
        """chat_model.invoke() returning AIMessage with usage_metadata populates usage."""
        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = "Hello!"
        mock_ai_msg.model_dump.return_value = {"type": "ai", "content": "Hello!"}
        mock_ai_msg.usage_metadata = {
            "input_tokens": 42,
            "output_tokens": 7,
            "input_token_details": {"cache_read": 3, "cache_creation": 1},
        }
        mock_model.invoke.return_value = mock_ai_msg

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

            result = ask_langchain("Hi")

        assert result["raw_response"]["usage"] == {
            "input_tokens": 42,
            "output_tokens": 7,
            "cache_read_input_tokens": 3,
            "cache_creation_input_tokens": 1,
        }
