"""conftest.py for langchain provider tests.

Injects sys.modules mocks so unit tests run without langchain installed.
Only injects mocks when the real packages are genuinely absent (ImportError).
This allows integration tests to use the real packages when installed.
"""

import sys

try:
    import langchain_anthropic  # noqa: F401
    import langchain_core  # noqa: F401
    import langchain_core.messages  # noqa: F401
    import langchain_google_genai  # noqa: F401
    import langchain_openai  # noqa: F401
except ImportError:
    from unittest.mock import MagicMock

    if "langchain_core" not in sys.modules:
        _lc_core = MagicMock()
        _lc_messages = MagicMock()
        _lc_core.messages = _lc_messages
        sys.modules["langchain_core"] = _lc_core
        sys.modules["langchain_core.messages"] = _lc_messages

    if "langchain_openai" not in sys.modules:
        sys.modules["langchain_openai"] = MagicMock()

    if "langchain_google_genai" not in sys.modules:
        sys.modules["langchain_google_genai"] = MagicMock()

    if "langchain_anthropic" not in sys.modules:
        sys.modules["langchain_anthropic"] = MagicMock()

    if "google.genai" not in sys.modules:
        if "google" not in sys.modules:
            sys.modules["google"] = MagicMock()
        sys.modules["google.genai"] = MagicMock()
