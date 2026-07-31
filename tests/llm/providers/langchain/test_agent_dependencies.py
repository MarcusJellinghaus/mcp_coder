"""Tests for the adapter capability check (``tool_interceptors`` support).

Covers the reusable ``_assert_tool_interceptors_supported()`` helper and its
invocation from ``_check_agent_dependencies()`` (issue I2.3, step 1).
"""

from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.agent import (
    _assert_tool_interceptors_supported,
    _check_agent_dependencies,
)

_CONVERT_TARGET = "langchain_mcp_adapters.tools.convert_mcp_tool_to_langchain_tool"


def _stub_without_interceptors(
    session: Any,
    tool: Any,
    *,
    connection: Optional[Any] = None,
    server_name: Optional[str] = None,
) -> Any:
    """Stand-in whose *real* signature omits ``tool_interceptors``."""
    return None


def _stub_with_interceptors(
    session: Any,
    tool: Any,
    *,
    connection: Optional[Any] = None,
    server_name: Optional[str] = None,
    tool_interceptors: Optional[Any] = None,
) -> Any:
    """Stand-in whose *real* signature includes ``tool_interceptors``."""
    return None


@pytest.mark.langchain_integration
def test_check_agent_dependencies_passes_with_supported_adapter() -> None:
    """Real install (>=0.3.0) exposes ``tool_interceptors`` -> no raise.

    Runs under the ``langchain_integration`` marker so the real package is
    present rather than the conftest ``MagicMock`` stand-in.
    """
    _check_agent_dependencies()


def test_assert_interceptors_rejects_missing_support() -> None:
    """A converter lacking ``tool_interceptors`` -> clear ImportError."""
    with patch(_CONVERT_TARGET, _stub_without_interceptors):
        with pytest.raises(ImportError, match="langchain-mcp-adapters>=0.3.0"):
            _assert_tool_interceptors_supported()


def test_assert_interceptors_accepts_supported_support() -> None:
    """A converter exposing ``tool_interceptors`` -> no raise."""
    with patch(_CONVERT_TARGET, _stub_with_interceptors):
        _assert_tool_interceptors_supported()


def test_assert_interceptors_skips_mock_stand_in() -> None:
    """A ``MagicMock`` stand-in (conftest injection) -> no raise.

    ``inspect.signature(MagicMock())`` reports ``(*args, **kwargs)``; the
    ``**kwargs`` guard treats that as capable rather than an unsupported adapter.
    """
    with patch(_CONVERT_TARGET, MagicMock()):
        _assert_tool_interceptors_supported()
