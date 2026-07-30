"""Tests for the langchain permission bridge (Step 3 of I2.3, TDD).

The provider-package bridge builds the langchain-specific deny shape so the
pure gateway never has to import ``langchain_core``. A denied MCP call becomes a
``ToolMessage(status="error")`` (langgraph's ``ToolNode`` fills in the real
``tool_call_id`` downstream).
"""

from __future__ import annotations

from mcp_coder.llm.providers.langchain.permission_bridge import (
    build_deny_tool_message,
)


def test_build_deny_tool_message_shape() -> None:
    """A deny message is a ToolMessage with the given content, error status, name."""
    msg = build_deny_tool_message("x", "t")

    assert msg.content == "x"
    assert msg.status == "error"
    assert msg.name == "t"


def test_build_deny_tool_message_is_tool_message() -> None:
    """The returned object is a langchain ToolMessage (``type == 'tool'``)."""
    msg = build_deny_tool_message("denied", "some_tool")

    assert msg.type == "tool"
