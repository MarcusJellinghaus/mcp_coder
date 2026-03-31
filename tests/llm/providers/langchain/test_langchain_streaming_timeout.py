"""Tests for inactivity timeout in _ask_text_stream chunk loop."""

import time
from collections.abc import Iterator
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


class TestTextStreamInactivityTimeout:
    """Inactivity timeout between chunks in _ask_text_stream."""

    def test_text_stream_inactivity_timeout(self) -> None:
        """Mock model yields one chunk then blocks; TimeoutError raised."""

        def _slow_stream(messages: object) -> Iterator[MagicMock]:
            yield _mock_chunk("first")
            time.sleep(2)  # exceeds timeout=1
            yield _mock_chunk("second")  # pragma: no cover

        mock_model = MagicMock()
        mock_model.stream.side_effect = _slow_stream

        with (
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import _ask_text_stream

            with pytest.raises(TimeoutError, match="No LLM output for 1s"):
                list(
                    _ask_text_stream(
                        question="Hi",
                        config=_make_config(),
                        backend="openai",
                        session_id="s1",
                        timeout=1,
                    )
                )

    def test_text_stream_active_no_timeout(self) -> None:
        """Model yields 3 chunks with no delay; all events received, no error."""
        chunks = [_mock_chunk("a"), _mock_chunk("b"), _mock_chunk("c")]
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)

        with (
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
        ):
            from mcp_coder.llm.providers.langchain import _ask_text_stream

            events = list(
                _ask_text_stream(
                    question="Hi",
                    config=_make_config(),
                    backend="openai",
                    session_id="s1",
                    timeout=2,
                )
            )

        text_deltas = [e for e in events if e["type"] == "text_delta"]
        assert len(text_deltas) == 3
        assert text_deltas[0]["text"] == "a"
        assert text_deltas[1]["text"] == "b"
        assert text_deltas[2]["text"] == "c"

        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) == 1
