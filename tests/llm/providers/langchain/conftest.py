"""conftest.py for langchain provider tests.

Injects sys.modules mocks so unit tests run without langchain installed.
Only injects mocks when the real packages are genuinely absent (ImportError).
This allows integration tests to use the real packages when installed.

Uses patch.dict for automatic cleanup so mocks never leak into other test
directories that may need real langchain imports.
"""

import sys
from collections.abc import AsyncIterator, Sequence
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest


def graph_events(
    final_messages: list[Any],
    inner: Sequence[dict[str, object]] = (),
) -> list[dict[str, object]]:
    """Wrap *inner* events in the root on_chain_start/on_chain_end pair.

    ``run_agent_stream`` captures the graph's final message list from the
    ``on_chain_end`` whose ``run_id`` matches the first ``on_chain_start``
    (matching by name would depend on version-specific LangGraph internals).
    This helper reproduces that shape: both bracket events share the run id
    ``"root"``, and the terminal one carries ``data.output.messages``.

    Args:
        final_messages: The graph's final message list, as delivered on the
            terminal event's ``data.output.messages``.
        inner: Events emitted between the two bracket events.

    Returns:
        The full event list to feed a stubbed ``astream_events``.
    """
    return [
        {
            "event": "on_chain_start",
            "run_id": "root",
            "name": "LangGraph",
            "data": {"input": {}},
        },
        *inner,
        {
            "event": "on_chain_end",
            "run_id": "root",
            "name": "LangGraph",
            "data": {"output": {"messages": list(final_messages)}},
        },
    ]


async def async_events(
    items: list[dict[str, object]],
) -> AsyncIterator[dict[str, object]]:
    """Create an async iterator from a list of event dicts.

    Mock-class rule for the react agent that consumes this: the stubbed agent
    must be a ``MagicMock()``, never an ``AsyncMock()``. ``run_agent_stream``
    does ``async for event in agent.astream_events(...)``, and an ``AsyncMock``
    child call returns a *coroutine*, which ``async for`` rejects before the
    return value is ever looked at.

    Yields:
        Each event dict in order.
    """
    for item in items:
        yield item


@pytest.fixture(autouse=True, scope="session")
def _mock_langchain_modules() -> Generator[None, None, None]:
    """Inject sys.modules mocks for any absent langchain packages.

    Only injects mocks for packages that are genuinely missing so that
    integration tests can use the real packages when installed.

    Uses patch.dict for automatic cleanup so mocks never leak into other
    test directories that may need real langchain imports.
    """

    # Create real classes for message types so isinstance() works in tests
    class _AIMessage:
        type = "ai"

        def __init__(self, **kwargs: object) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self) -> dict[str, object]:
            return {"type": self.type, "content": getattr(self, "content", "")}

    class _HumanMessage:
        type = "human"

        def __init__(self, **kwargs: object) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self) -> dict[str, object]:
            return {"type": self.type, "content": getattr(self, "content", "")}

    class _SystemMessage:
        type = "system"

        def __init__(self, **kwargs: object) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self) -> dict[str, object]:
            return {"type": self.type, "content": getattr(self, "content", "")}

    class _ToolMessage:
        type = "tool"

        def __init__(self, **kwargs: object) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self) -> dict[str, object]:
            return {"type": self.type, "content": getattr(self, "content", "")}

    def _messages_from_dict(
        messages: list[dict[str, object]],
    ) -> list[object]:
        """Stub for langchain_core.messages.messages_from_dict."""
        _type_map = {"human": _HumanMessage, "ai": _AIMessage, "tool": _ToolMessage}
        result = []
        for m in messages:
            msg_type = str(m.get("type", "human"))
            data = m.get("data", {})
            cls = _type_map.get(msg_type, _HumanMessage)
            result.append(cls(**(data if isinstance(data, dict) else {})))
        return result

    _lc_messages = MagicMock()
    _lc_messages.AIMessage = _AIMessage
    _lc_messages.HumanMessage = _HumanMessage
    _lc_messages.SystemMessage = _SystemMessage
    _lc_messages.ToolMessage = _ToolMessage
    _lc_messages.messages_from_dict = _messages_from_dict

    mocks: dict[str, MagicMock] = {}

    if "langchain_core" not in sys.modules:
        _lc_core = MagicMock()
        _lc_core.messages = _lc_messages
        mocks["langchain_core"] = _lc_core
        mocks["langchain_core.messages"] = _lc_messages
    elif "langchain_core.messages" not in sys.modules:
        mocks["langchain_core.messages"] = _lc_messages

    if "langchain_openai" not in sys.modules:
        mocks["langchain_openai"] = MagicMock()

    if "langchain_google_genai" not in sys.modules:
        mocks["langchain_google_genai"] = MagicMock()

    if "langchain_anthropic" not in sys.modules:
        mocks["langchain_anthropic"] = MagicMock()

    if "langchain_ollama" not in sys.modules:
        mocks["langchain_ollama"] = MagicMock()

    if "ollama" not in sys.modules:
        mocks["ollama"] = MagicMock()

    if "langchain_mcp_adapters" not in sys.modules:
        mocks["langchain_mcp_adapters"] = MagicMock()
        mocks["langchain_mcp_adapters.client"] = MagicMock()
        mocks["langchain_mcp_adapters.tools"] = MagicMock()

    if "langgraph" not in sys.modules:
        mocks["langgraph"] = MagicMock()
        mocks["langgraph.prebuilt"] = MagicMock()

    if "google.genai" not in sys.modules:
        if "google" not in sys.modules:
            mocks["google"] = MagicMock()
        mocks["google.genai"] = MagicMock()

    if "httpx" not in sys.modules:
        mocks["httpx"] = MagicMock()

    if not mocks:
        yield
        return

    with patch.dict(sys.modules, mocks):
        yield
