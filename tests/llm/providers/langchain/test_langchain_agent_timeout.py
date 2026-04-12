"""Tests for inactivity timeout in _ask_agent_stream queue loop."""

import queue
from unittest.mock import MagicMock, patch

import pytest

_MOD_LC = "mcp_coder.llm.providers.langchain"
_MOD_AGENT = "mcp_coder.llm.providers.langchain.agent"


def _make_config(backend: str = "openai") -> dict[str, str | None]:
    return {
        "provider": "langchain",
        "backend": backend,
        "model": "gpt-4o",
        "api_key": None,
        "endpoint": None,
        "api_version": None,
    }


class TestAgentStreamInactivityTimeout:
    """Inactivity timeout when agent queue produces no events."""

    def test_agent_stream_inactivity_timeout(self) -> None:
        """Queue never receives an event; TimeoutError raised."""
        mock_model = MagicMock()

        # Create an empty queue that will always raise queue.Empty on get()
        empty_queue: queue.Queue[object] = queue.Queue()

        with (
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}.ensure_truststore"),
            patch(f"{_MOD_AGENT}._check_agent_dependencies"),
            patch(f"{_MOD_LC}.queue.Queue", return_value=empty_queue),
            patch(f"{_MOD_LC}.threading.Thread") as mock_thread_cls,
        ):
            # Make the thread start() a no-op (no async agent runs)
            mock_thread = MagicMock()
            mock_thread_cls.return_value = mock_thread

            from mcp_coder.llm.providers.langchain import _ask_agent_stream

            with pytest.raises(
                TimeoutError,
                match=r"LLM inactivity timeout \(langchain\): no response for \d+s\. Connection closed\.",
            ):
                list(
                    _ask_agent_stream(
                        question="Hi",
                        config=_make_config(),
                        session_id="s1",
                        mcp_config=".mcp.json",
                        timeout=1,
                    )
                )
