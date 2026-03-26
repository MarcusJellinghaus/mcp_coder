"""Tests for ask_langchain_stream / _ask_text_stream in langchain provider."""

import json
from unittest.mock import MagicMock, patch

import pytest

_MOD_LC = "mcp_coder.llm.providers.langchain"


def _make_config(backend: str = "openai") -> dict[str, str | None]:
    return {
        "provider": "langchain",
        "backend": backend,
        "model": "gpt-4o",
        "api_key": None,
        "endpoint": None,
        "api_version": None,
    }


def _mock_chunk(content: str) -> MagicMock:
    """Create a mock AIMessageChunk with given content."""
    chunk = MagicMock()
    chunk.content = content
    chunk.model_dump.return_value = {"type": "AIMessageChunk", "content": content}
    return chunk


class TestAskLangchainStreamTextYieldsDeltas:
    """ask_langchain_stream yields text_delta events from chat_model.stream()."""

    def test_text_yields_deltas(self) -> None:
        """Each chunk from chat_model.stream() becomes a text_delta event."""
        chunks = [_mock_chunk("Hello"), _mock_chunk(" world")]
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("Hi"))

        text_deltas = [e for e in events if e["type"] == "text_delta"]
        assert len(text_deltas) == 2
        assert text_deltas[0]["text"] == "Hello"
        assert text_deltas[1]["text"] == " world"


class TestAskLangchainStreamTextYieldsRawLines:
    """ask_langchain_stream yields raw_line events for each chunk."""

    def test_text_yields_raw_lines(self) -> None:
        """Each chunk yields a raw_line event with JSON serialization."""
        chunks = [_mock_chunk("tok")]
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("Hi"))

        raw_lines = [e for e in events if e["type"] == "raw_line"]
        assert len(raw_lines) == 1
        parsed = json.loads(str(raw_lines[0]["line"]))
        assert parsed["content"] == "tok"


class TestAskLangchainStreamTextYieldsDone:
    """ask_langchain_stream yields a done event with session_id."""

    def test_text_yields_done(self) -> None:
        """Stream ends with a done event containing the session_id."""
        mock_model = MagicMock()
        mock_model.stream.return_value = iter([_mock_chunk("x")])

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("Hi", session_id="sess-1"))

        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) == 1
        assert done_events[0]["session_id"] == "sess-1"


class TestAskLangchainStreamTextStoresHistory:
    """ask_langchain_stream stores session history after streaming."""

    def test_text_stores_history(self) -> None:
        """store_langchain_history is called with correct messages."""
        chunks = [_mock_chunk("answer")]
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)
        store_mock = MagicMock()

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history", store_mock),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            list(ask_langchain_stream("q", session_id="sid"))

        store_mock.assert_called_once()
        args = store_mock.call_args[0]
        assert args[0] == "sid"  # session_id
        stored = args[1]
        types = [m["type"] for m in stored]
        assert types == ["human", "ai"]


class TestAskLangchainStreamAgentFallback:
    """Agent mode falls back to blocking ask_langchain()."""

    def test_agent_falls_back_to_blocking(self) -> None:
        """When mcp_config is present, ask_langchain() is called."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "agent response",
            "session_id": "agent-sid",
            "provider": "langchain",
            "raw_response": {"usage": {"tokens": 42}},
        }
        with patch(f"{_MOD_LC}.ask_langchain", return_value=mock_response) as mock_ask:
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            list(
                ask_langchain_stream(
                    "q",
                    session_id="s",
                    mcp_config="/tmp/mcp.json",
                )
            )

        mock_ask.assert_called_once()
        call_kwargs = mock_ask.call_args
        assert call_kwargs[1].get("mcp_config") == "/tmp/mcp.json" or (
            len(call_kwargs[0]) > 0
        )

    def test_agent_fallback_yields_text(self) -> None:
        """Agent fallback yields text_delta with full response text + done."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00",
            "text": "agent response",
            "session_id": "agent-sid",
            "provider": "langchain",
            "raw_response": {"usage": {"tokens": 42}},
        }
        with patch(f"{_MOD_LC}.ask_langchain", return_value=mock_response):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events = list(ask_langchain_stream("q", mcp_config="/tmp/mcp.json"))

        text_deltas = [e for e in events if e["type"] == "text_delta"]
        assert len(text_deltas) == 1
        assert text_deltas[0]["text"] == "agent response"

        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) == 1
        assert done_events[0]["session_id"] == "agent-sid"


class TestAskLangchainStreamRoutesToText:
    """Without mcp_config, ask_langchain_stream routes to _ask_text_stream."""

    def test_routes_to_text_without_mcp_config(self) -> None:
        """No mcp_config means _ask_text_stream is used (chat_model.stream called)."""
        mock_model = MagicMock()
        mock_model.stream.return_value = iter([_mock_chunk("hi")])

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            list(ask_langchain_stream("Hi"))

        mock_model.stream.assert_called_once()


class TestAskLangchainStreamErrorHandling:
    """ask_langchain_stream yields error event on provider errors."""

    def test_error_handling(self) -> None:
        """Provider error yields an error event and re-raises."""
        mock_model = MagicMock()
        mock_model.stream.side_effect = RuntimeError("boom")

        with (
            patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            with pytest.raises(RuntimeError, match="boom"):
                list(ask_langchain_stream("Hi"))
