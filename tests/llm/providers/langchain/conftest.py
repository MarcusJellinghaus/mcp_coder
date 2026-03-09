"""conftest.py for langchain provider tests.

Injects sys.modules mocks so unit tests run without langchain installed.
All mocks are injected at module level (before any test collection),
so source modules can be imported even when langchain packages are absent.
"""

import sys
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
