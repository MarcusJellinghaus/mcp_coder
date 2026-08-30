"""Tests for step 10 — connection errors name the host actually dialed.

The host must be read off the *constructed client* via
``_config_diagnostics.dialed_url``, never computed from config: a
config-derived value is wrong the moment ``OPENAI_BASE_URL`` or
``OLLAMA_HOST`` redirects the request, which is precisely the situation a
connection error has to explain. Every provider-path test below therefore
leaves ``config["base_url"]`` unset while the stub client reports
:data:`_DIALED`, so an assertion on that URL can only pass if the value came
from the client.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain import _handle_provider_error
from mcp_coder.llm.providers.langchain._exceptions import (
    LLMAuthError,
    LLMConnectionError,
)

_MOD = "mcp_coder.llm.providers.langchain"

#: Names *consumed* by the moved setup helpers resolve through ``_setup``'s
#: globals, so patching them on the package would silently no-op.
_SETUP = f"{_MOD}._setup"

#: What the stub client reports; deliberately not any config value.
_DIALED = "https://relay.internal/v1"

#: The static per-backend hint that ``dialed`` accompanies but never replaces.
_STATIC_OPENAI_HINT = "base_url if using a custom server"

#: How a known dialed URL is rendered — on its own line, distinct from the
#: ``base_url:`` hint, which says what to change rather than what happened.
_DIALED_LINE = "Requests were sent to: "


class _StubRootClient:
    """The openai SDK client hanging off ChatOpenAI.root_client."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url


class _StubChatModel:
    """A constructed chat model that exposes a dialed URL and fails to talk.

    ``invoke`` / ``stream`` raise so the provider paths reach their error
    handlers; ``root_client.base_url`` is what those handlers must report.
    """

    def __init__(self, url: str = _DIALED) -> None:
        self.root_client = _StubRootClient(url)

    def invoke(self, _messages: Any) -> Any:
        raise ConnectionError("Connection refused")

    def stream(self, _messages: Any) -> Any:
        raise ConnectionError("Connection refused")


class _FakeAuthError(Exception):
    """Stand-in for an SDK authentication error."""


class _RaisingAsyncIter:
    """An ``async for`` source that fails on first advance.

    A ``raise``-then-``yield`` coroutine would be the shorter spelling but
    leaves the ``yield`` unreachable; this shape is the one
    ``test_langchain_agent_streaming.py`` already uses.
    """

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def __aiter__(self) -> "_RaisingAsyncIter":
        return self

    async def __anext__(self) -> dict[str, object]:
        raise self._exc


def _make_config(backend: str = "openai") -> dict[str, str | None]:
    """Config with **no** base_url, so only the client can supply one."""
    return {
        "provider": "langchain",
        "backend": backend,
        "model": "gpt-4o",
        "api_key": None,
        "base_url": None,
        "api_version": None,
    }


# ---------------------------------------------------------------------------
# Cases 1 & 2 — _handle_provider_error's new argument
# ---------------------------------------------------------------------------


class TestHandleProviderErrorDialed:
    """The ``dialed`` argument accompanies the static base_url hint."""

    def test_dialed_named_in_connection_message(self) -> None:
        """Case 1: the raised message contains the dialed URL *and* the hint."""
        with pytest.raises(LLMConnectionError) as exc_info:
            _handle_provider_error(ConnectionError("boom"), "openai", _DIALED)
        message = str(exc_info.value)
        assert f"{_DIALED_LINE}{_DIALED}" in message
        assert f"base_url: {_STATIC_OPENAI_HINT}" in message

    def test_dialed_line_is_distinct_from_the_base_url_hint(self) -> None:
        """The dialed URL never occupies the ``base_url:`` slot."""
        with pytest.raises(LLMConnectionError) as exc_info:
            _handle_provider_error(ConnectionError("boom"), "openai", _DIALED)
        assert str(exc_info.value) == (
            "Connection to OpenAI API failed: boom\n"
            f"{_DIALED_LINE}{_DIALED}\n"
            "Check:\n"
            "  1. OPENAI_API_KEY env var or api_key in config.toml\n"
            f"  2. base_url: {_STATIC_OPENAI_HINT}\n"
            "  3. Network/firewall/proxy settings"
        )

    def test_default_none_keeps_todays_message(self) -> None:
        """Case 2: regression guard — the whole message is unchanged."""
        with pytest.raises(LLMConnectionError) as exc_info:
            _handle_provider_error(ConnectionError("boom"), "openai")
        assert str(exc_info.value) == (
            "Connection to OpenAI API failed: boom\n"
            "Check:\n"
            "  1. OPENAI_API_KEY env var or api_key in config.toml\n"
            f"  2. base_url: {_STATIC_OPENAI_HINT}\n"
            "  3. Network/firewall/proxy settings"
        )

    def test_empty_dialed_prints_no_dialed_line(self) -> None:
        """An empty string is not a host; emit no dialed line at all."""
        with pytest.raises(LLMConnectionError) as exc_info:
            _handle_provider_error(ConnectionError("boom"), "openai", "")
        message = str(exc_info.value)
        assert _DIALED_LINE not in message
        assert _STATIC_OPENAI_HINT in message

    def test_ollama_keeps_its_hint_beside_the_dialed_host(self) -> None:
        """The OLLAMA_HOST guidance survives — the URL cannot replace it."""
        with pytest.raises(LLMConnectionError) as exc_info:
            _handle_provider_error(
                ConnectionError("boom"), "ollama", "http://box:11434"
            )
        message = str(exc_info.value)
        assert f"{_DIALED_LINE}http://box:11434" in message
        assert "base_url/OLLAMA_HOST if not localhost" in message

    def test_backend_without_a_hint_has_no_base_url_line(self) -> None:
        """anthropic has an empty static hint, so only the dialed line appears."""
        with pytest.raises(LLMConnectionError) as exc_info:
            _handle_provider_error(ConnectionError("boom"), "anthropic", _DIALED)
        message = str(exc_info.value)
        assert f"{_DIALED_LINE}{_DIALED}" in message
        assert "base_url:" not in message

    def test_auth_errors_do_not_mention_the_host(self) -> None:
        """The auth message has no base_url line to carry it."""
        with (
            patch(f"{_SETUP}.OPENAI_AUTH_ERRORS", (_FakeAuthError,)),
            pytest.raises(LLMAuthError) as exc_info,
        ):
            _handle_provider_error(_FakeAuthError("nope"), "openai", _DIALED)
        assert _DIALED not in str(exc_info.value)

    def test_gemini_non_auth_client_error_names_the_host(self) -> None:
        """The second connection-error branch uses the same hint."""
        with (
            patch(f"{_SETUP}.GOOGLE_CLIENT_ERRORS", (_FakeAuthError,)),
            patch(f"{_SETUP}.is_google_auth_error", return_value=False),
            pytest.raises(LLMConnectionError) as exc_info,
        ):
            _handle_provider_error(_FakeAuthError("503"), "gemini", _DIALED)
        assert f"{_DIALED_LINE}{_DIALED}" in str(exc_info.value)

    def test_unrelated_exception_still_returns(self) -> None:
        """A non-connection, non-auth error is not rewrapped."""
        _handle_provider_error(FileNotFoundError("nope"), "openai", _DIALED)


# ---------------------------------------------------------------------------
# Case 3 — all four provider paths thread the dialed URL
# ---------------------------------------------------------------------------


class TestProviderPathsNameTheDialedHost:
    """Case 3: text, agent, text-stream and agent-stream all pass ``dialed``."""

    def test_ask_text(self) -> None:
        """_ask_text reads the URL off the model it just constructed."""
        with (
            patch(f"{_MOD}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=_StubChatModel()),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(LLMConnectionError) as exc_info:
                ask_langchain("question")
        assert f"{_DIALED_LINE}{_DIALED}" in str(exc_info.value)

    def test_ask_text_stream(self) -> None:
        """_ask_text_stream does the same on the streaming path."""
        with (
            patch(f"{_MOD}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=_StubChatModel()),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            with pytest.raises(LLMConnectionError) as exc_info:
                list(ask_langchain_stream("question"))
        assert f"{_DIALED_LINE}{_DIALED}" in str(exc_info.value)

    def test_ask_agent(self) -> None:
        """_ask_agent names the host when run_agent fails to connect."""
        with (
            patch(f"{_MOD}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=_StubChatModel()),
            patch(f"{_MOD}.agent._check_agent_dependencies"),
            patch(
                f"{_MOD}.agent.run_agent",
                new_callable=AsyncMock,
                side_effect=ConnectionError("Connection refused"),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(LLMConnectionError) as exc_info:
                ask_langchain("question", mcp_config="/tmp/mcp.json")
        assert f"{_DIALED_LINE}{_DIALED}" in str(exc_info.value)

    def test_ask_agent_stream(self) -> None:
        """_ask_agent_stream names the host on the held thread exception."""

        def _raising_stream(**_kwargs: Any) -> _RaisingAsyncIter:
            return _RaisingAsyncIter(ConnectionError("Connection refused"))

        with (
            patch(f"{_MOD}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=_StubChatModel()),
            patch(f"{_MOD}.agent._check_agent_dependencies"),
            patch(f"{_MOD}.agent.run_agent_stream", _raising_stream),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            with pytest.raises(LLMConnectionError) as exc_info:
                list(ask_langchain_stream("question", mcp_config="/tmp/mcp.json"))
        assert f"{_DIALED_LINE}{_DIALED}" in str(exc_info.value)

    def test_client_without_a_url_keeps_the_static_hint(self) -> None:
        """dialed_url() returning None must not degrade today's message."""
        model = MagicMock(spec=["invoke"])
        model.invoke.side_effect = ConnectionError("Connection refused")
        with (
            patch(f"{_MOD}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=model),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(LLMConnectionError) as exc_info:
                ask_langchain("question")
        message = str(exc_info.value)
        assert _DIALED_LINE not in message
        assert _STATIC_OPENAI_HINT in message


# ---------------------------------------------------------------------------
# Case 4 — --check-models
# ---------------------------------------------------------------------------


class TestCheckModelsNamesTheBaseUrl:
    """Case 4: the model-listing connection branch names the URL it used."""

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_connection_error_names_base_url(self, mock_list: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_list.side_effect = LLMConnectionError("Connection to OpenAI API failed")
        result = _list_models_for_backend("openai", "sk-test", _DIALED)
        assert result["error_type"] == "connection"
        assert f"tried {_DIALED}" in result["error"]

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_message_unchanged_without_a_base_url(self, mock_list: MagicMock) -> None:
        """Nothing is invented when no URL was handed to the SDK."""
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        msg = "Connection to OpenAI API failed: boom"
        mock_list.side_effect = LLMConnectionError(msg)
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["error"] == msg

    @patch("mcp_coder.llm.providers.langchain._models.list_ollama_models")
    def test_ollama_connection_error_names_base_url(self, mock_list: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_list.side_effect = LLMConnectionError("Connection to Ollama API failed")
        result = _list_models_for_backend("ollama", None, "http://box:11434")
        assert "tried http://box:11434" in result["error"]

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_auth_error_message_is_untouched(self, mock_list: MagicMock) -> None:
        """Only the connection branch changed."""
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        msg = "Authentication to OpenAI API failed: invalid key"
        mock_list.side_effect = LLMAuthError(msg)
        result = _list_models_for_backend("openai", "sk-test", _DIALED)
        assert result["error"] == msg
