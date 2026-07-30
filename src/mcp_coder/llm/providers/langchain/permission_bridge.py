"""Langchain deny-shape bridge for the iCoder permission gateway.

Keeps ``langchain_core`` confined to the provider package: the pure gateway
(:mod:`mcp_coder.icoder.permissions.gateway`) calls
:func:`build_deny_tool_message` rather than constructing the langchain
``ToolMessage`` itself, so it never has to import ``langchain_core``.
"""

from __future__ import annotations

from typing import Any


def build_deny_tool_message(text: str, name: str) -> Any:
    """Return a langchain ``ToolMessage(status="error")`` for a denied MCP call.

    Args:
        text: The human-readable denial reason (becomes the message content).
        name: The bare tool name the denied call targeted.

    Returns:
        A ``ToolMessage`` with ``status="error"``. ``tool_call_id`` is left
        empty because langgraph's ``ToolNode`` overwrites it with the real
        call id downstream.
    """
    from langchain_core.messages import ToolMessage  # pylint: disable=import-error

    return ToolMessage(content=text, status="error", tool_call_id="", name=name)
