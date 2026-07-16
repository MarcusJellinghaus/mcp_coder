"""Tests for the pure ``filter_tools_by_declaration`` matching function.

These tests exercise the MCPManager-free filter in isolation: tools are tiny
stubs and ``canonical_name_of`` is a trivial accessor, so no live MCP
connection is required.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from mcp_coder.llm.providers.langchain.mcp_manager import (
    filter_tools_by_declaration,
)


def _tool(canonical: str | None) -> SimpleNamespace:
    """Create a stub tool exposing a ``canonical`` attribute."""
    return SimpleNamespace(canonical=canonical)


def _canonical_of(tool: Any) -> str | None:
    """Read the stub tool's canonical name."""
    return tool.canonical  # type: ignore[no-any-return]


def test_subset_kept_undeclared_dropped() -> None:
    """Only declared exact tokens survive; undeclared tools are dropped."""
    tools = [
        _tool("mcp__srv__read_file"),
        _tool("mcp__srv__write_file"),
        _tool("mcp__srv__delete_file"),
    ]
    declared = ("mcp__srv__read_file", "mcp__srv__write_file")

    filtered, warnings = filter_tools_by_declaration(tools, _canonical_of, declared)

    assert [t.canonical for t in filtered] == [
        "mcp__srv__read_file",
        "mcp__srv__write_file",
    ]
    assert warnings == []


def test_empty_mcp_allow_set_yields_no_tools() -> None:
    """A Bash-only declaration narrows to zero MCP tools, no warning."""
    tools = [_tool("mcp__srv__read_file"), _tool("mcp__srv__write_file")]
    declared = ("Bash(git add *)",)

    filtered, warnings = filter_tools_by_declaration(tools, _canonical_of, declared)

    assert filtered == []
    assert warnings == []


def test_unknown_declared_tool_dropped_no_warning() -> None:
    """An exact token that matches nothing is simply dropped, no warning."""
    tools = [_tool("mcp__srv__read_file")]
    declared = ("mcp__srv__nope",)

    filtered, warnings = filter_tools_by_declaration(tools, _canonical_of, declared)

    assert filtered == []
    assert warnings == []


def test_wildcard_token_not_matched_and_warns() -> None:
    """A wildcard token never widens the set and produces a warning."""
    tools = [_tool("mcp__srv__read_file"), _tool("mcp__srv__write_file")]
    declared = ("mcp__srv__*",)

    filtered, warnings = filter_tools_by_declaration(tools, _canonical_of, declared)

    assert filtered == []
    assert len(warnings) == 1
    assert "mcp__srv__*" in warnings[0]


def test_group_token_not_matched_and_warns() -> None:
    """An ``@group`` token never widens the set and produces a warning."""
    tools = [_tool("mcp__srv__read_file")]
    declared = ("@dev",)

    filtered, warnings = filter_tools_by_declaration(tools, _canonical_of, declared)

    assert filtered == []
    assert len(warnings) == 1
    assert "@dev" in warnings[0]


def test_arg_scoped_token_not_matched_and_warns() -> None:
    """An arg-scoped token never widens the set and produces a warning."""
    tools = [_tool("mcp__srv__tool")]
    declared = ("mcp__srv__tool(command=push)",)

    filtered, warnings = filter_tools_by_declaration(tools, _canonical_of, declared)

    assert filtered == []
    assert len(warnings) == 1
    assert "mcp__srv__tool(command=push)" in warnings[0]


def test_same_bare_name_different_canonical_disambiguated() -> None:
    """Two tools sharing a bare name: only the declared canonical is kept."""
    tools = [
        _tool("mcp__srv_a__read_file"),
        _tool("mcp__srv_b__read_file"),
    ]
    declared = ("mcp__srv_a__read_file",)

    filtered, warnings = filter_tools_by_declaration(tools, _canonical_of, declared)

    assert [t.canonical for t in filtered] == ["mcp__srv_a__read_file"]
    assert warnings == []


def test_input_list_not_mutated() -> None:
    """The input tool list is never mutated; a new list is returned."""
    tools = [_tool("mcp__srv__read_file"), _tool("mcp__srv__write_file")]
    original = list(tools)
    declared = ("mcp__srv__read_file",)

    filtered, _ = filter_tools_by_declaration(tools, _canonical_of, declared)

    assert tools == original
    assert len(tools) == 2
    assert filtered is not tools


def test_canonical_name_none_dropped() -> None:
    """A tool whose canonical name is ``None`` is dropped."""
    tools = [_tool(None), _tool("mcp__srv__read_file")]
    declared = ("mcp__srv__read_file",)

    filtered, warnings = filter_tools_by_declaration(tools, _canonical_of, declared)

    assert [t.canonical for t in filtered] == ["mcp__srv__read_file"]
    assert warnings == []
