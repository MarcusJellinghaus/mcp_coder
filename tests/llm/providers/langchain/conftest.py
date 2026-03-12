"""conftest.py for langchain provider tests.

Injects sys.modules mocks so unit tests run without langchain installed.
Only injects mocks when the real packages are genuinely absent (ImportError).
This allows integration tests to use the real packages when installed.

Uses patch.dict for automatic cleanup so mocks never leak into other test
directories that may need real langchain imports.
"""

import sys
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

_LANGCHAIN_AVAILABLE = True
try:
    import langchain_anthropic  # noqa: F401
    import langchain_core  # noqa: F401
    import langchain_core.messages  # noqa: F401
    import langchain_google_genai  # noqa: F401
    import langchain_openai  # noqa: F401
except ImportError:
    _LANGCHAIN_AVAILABLE = False


@pytest.fixture(autouse=True, scope="session")
def _mock_langchain_modules() -> Generator[None, None, None]:
    """Inject sys.modules mocks only when real packages are absent.

    Uses patch.dict so sys.modules is automatically restored on teardown.
    """
    if _LANGCHAIN_AVAILABLE:
        yield
        return

    # Create real classes for message types so isinstance() works in tests
    class _AIMessage:
        def __init__(self, **kwargs: object) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

    class _HumanMessage:
        def __init__(self, **kwargs: object) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

    class _ToolMessage:
        def __init__(self, **kwargs: object) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

    _lc_core = MagicMock()
    _lc_messages = MagicMock()
    _lc_messages.AIMessage = _AIMessage
    _lc_messages.HumanMessage = _HumanMessage
    _lc_messages.ToolMessage = _ToolMessage
    _lc_core.messages = _lc_messages

    mocks: dict[str, MagicMock] = {}

    if "langchain_core" not in sys.modules:
        mocks["langchain_core"] = _lc_core
        mocks["langchain_core.messages"] = _lc_messages

    if "langchain_openai" not in sys.modules:
        mocks["langchain_openai"] = MagicMock()

    if "langchain_google_genai" not in sys.modules:
        mocks["langchain_google_genai"] = MagicMock()

    if "langchain_anthropic" not in sys.modules:
        mocks["langchain_anthropic"] = MagicMock()

    if "langchain_mcp_adapters" not in sys.modules:
        _lc_mcp = MagicMock()
        mocks["langchain_mcp_adapters"] = _lc_mcp
        mocks["langchain_mcp_adapters.client"] = MagicMock()

    if "langgraph" not in sys.modules:
        _langgraph = MagicMock()
        mocks["langgraph"] = _langgraph
        mocks["langgraph.prebuilt"] = MagicMock()

    if "google.genai" not in sys.modules:
        if "google" not in sys.modules:
            mocks["google"] = MagicMock()
        mocks["google.genai"] = MagicMock()

    with patch.dict(sys.modules, mocks):
        yield
