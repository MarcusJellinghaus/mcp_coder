"""conftest.py for langchain provider tests.

Injects sys.modules mocks so unit tests run without langchain installed.
Only injects mocks when the real packages are genuinely absent (ImportError).
This allows integration tests to use the real packages when installed.

Uses patch.dict for automatic cleanup so mocks never leak into other test
directories that may need real langchain imports.
"""

import importlib.util
import sys
from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest


def _is_installed(name: str) -> bool:
    """Return True when *name* is genuinely importable.

    Membership in ``sys.modules`` is not a usable proxy: an installed package
    that simply has not been imported yet is absent from ``sys.modules``, and
    mocking over it makes the real package unreachable for the rest of the
    session (this fixture is session-scoped, so its ``patch.dict`` outlives the
    tests in this directory). That is what wedged the ``langchain-integration``
    CI job, whose graph-level tests need the real adapter and ``langchain_core``.
    """
    if name in sys.modules:
        return True
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        # Parent package missing (ModuleNotFoundError) or not a package.
        return False


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


@pytest.fixture(autouse=True)
def _tmp_home(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Point ``Path.home()`` at *tmp_path* for the unit tests in this directory.

    Session storage resolves ``~/.mcp_coder/sessions/langchain`` through
    ``Path.home()`` at call time, so every test that reaches
    ``langchain_history_exists`` - which is every ``run_agent_stream`` test
    whose event list has no terminal ``on_chain_end`` - otherwise reads the
    developer's real home directory. Patching that test by test was
    whack-a-mole; one redirect for the directory closes the class.

    The fixture requests the same function-scoped ``tmp_path`` the test gets,
    so a test can still seed history with ``store_langchain_history`` and then
    find (or assert the absence of) the file under its own ``tmp_path``.

    This only moves the home directory. It does not touch the resume guard,
    which stays opt-in through ``skip_langchain_history_guard``.

    Args:
        request: Used to exempt ``langchain_integration`` tests. Those load
            real credentials from ``~/.mcp_coder/config.toml``, and a
            redirected home would turn the whole suite into silent skips.
        monkeypatch: Undoes the redirect after the test.
        tmp_path: The per-test directory that stands in for the home directory.
    """
    if request.node.get_closest_marker("langchain_integration"):
        return
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))


@pytest.fixture
def skip_langchain_history_guard() -> Generator[None, None, None]:
    """Neutralise the resume guard for tests that use synthetic session ids.

    Opt-in on purpose: an autouse version would also disable the guard for
    the langchain_integration resume tests in test_langchain_integration.py,
    which are the only end-to-end path where a real history file is written
    and then resumed. Those tests must run with the guard live.

    Yields:
        None, with the guard patched out for the duration of the test.
    """
    with patch("mcp_coder.llm.providers.langchain._setup.require_langchain_history"):
        yield


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

    if not _is_installed("langchain_core"):
        _lc_core = MagicMock()
        _lc_core.messages = _lc_messages
        mocks["langchain_core"] = _lc_core
        mocks["langchain_core.messages"] = _lc_messages
    elif not _is_installed("langchain_core.messages"):
        mocks["langchain_core.messages"] = _lc_messages

    if not _is_installed("langchain_openai"):
        mocks["langchain_openai"] = MagicMock()

    if not _is_installed("langchain_google_genai"):
        mocks["langchain_google_genai"] = MagicMock()

    if not _is_installed("langchain_anthropic"):
        mocks["langchain_anthropic"] = MagicMock()

    if not _is_installed("langchain_ollama"):
        mocks["langchain_ollama"] = MagicMock()

    if not _is_installed("ollama"):
        mocks["ollama"] = MagicMock()

    if not _is_installed("langchain_mcp_adapters"):
        mocks["langchain_mcp_adapters"] = MagicMock()
        mocks["langchain_mcp_adapters.client"] = MagicMock()
        mocks["langchain_mcp_adapters.tools"] = MagicMock()

    if not _is_installed("langgraph"):
        mocks["langgraph"] = MagicMock()
        mocks["langgraph.prebuilt"] = MagicMock()

    if not _is_installed("google.genai"):
        if not _is_installed("google"):
            mocks["google"] = MagicMock()
        mocks["google.genai"] = MagicMock()

    if not _is_installed("httpx"):
        mocks["httpx"] = MagicMock()

    if not mocks:
        yield
        return

    with patch.dict(sys.modules, mocks):
        yield
