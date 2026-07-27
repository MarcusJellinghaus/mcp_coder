#!/usr/bin/env python3
"""Tests for the pure MCP guard helpers (claude_mcp_guard.py).

Split from test_claude_cli_stream_mcp_guard.py to keep file sizes manageable.
Covers find_unavailable_mcp_servers, find_fatal_mcp_servers,
find_exposed_mcp_tools and load_mcp_server_names; the guard behaviour inside
the blocking and streaming code paths stays in
test_claude_cli_stream_mcp_guard.py.
"""

import json
from pathlib import Path
from typing import cast

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    MCP_NEEDS_AUTH_STATUS,
    StreamMessage,
    find_exposed_mcp_tools,
    find_fatal_mcp_servers,
    find_unavailable_mcp_servers,
    load_mcp_server_names,
)


class TestFindUnavailableMcpServers:
    """Tests for the MCP server availability guard (find_unavailable_mcp_servers)."""

    def test_none_system_message_returns_empty(self) -> None:
        assert find_unavailable_mcp_servers(None) == {}

    def test_no_servers_configured_returns_empty(self) -> None:
        msg = cast(StreamMessage, {"type": "system", "subtype": "init", "tools": []})
        assert find_unavailable_mcp_servers(msg) == {}

    def test_all_connected_returns_empty(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "connected"},
                    {"name": "mcp-workspace", "status": "connected"},
                ],
            },
        )
        assert find_unavailable_mcp_servers(msg) == {}

    def test_failed_and_pending_are_reported(self) -> None:
        """Reproduces the #995 init: mcp-tools-py failed, mcp-workspace pending."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "failed"},
                    {"name": "mcp-workspace", "status": "pending"},
                ],
            },
        )
        assert find_unavailable_mcp_servers(msg) == {
            "mcp-tools-py": "failed",
            "mcp-workspace": "pending",
        }

    def test_only_unavailable_servers_reported(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "connected"},
                    {"name": "mcp-workspace", "status": "failed"},
                ],
            },
        )
        assert find_unavailable_mcp_servers(msg) == {"mcp-workspace": "failed"}

    def test_missing_status_treated_as_unavailable(self) -> None:
        msg = cast(
            StreamMessage,
            {"type": "system", "subtype": "init", "mcp_servers": [{"name": "x"}]},
        )
        assert find_unavailable_mcp_servers(msg) == {"x": "unknown"}

    def test_needs_auth_is_reported(self) -> None:
        """Unauthenticated account connectors stay visible to reporting consumers."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "a", "status": "connected"},
                    {"name": "b", "status": "pending"},
                    {"name": "c", "status": "needs-auth"},
                ],
            },
        )
        assert find_unavailable_mcp_servers(msg) == {
            "b": "pending",
            "c": MCP_NEEDS_AUTH_STATUS,
        }

    def test_status_is_case_insensitive(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [{"name": "mcp-workspace", "status": "Connected"}],
            },
        )
        assert find_unavailable_mcp_servers(msg) == {}


class TestFindFatalMcpServers:
    """find_fatal_mcp_servers reports only terminal (non-pending) servers."""

    def test_none_system_message_returns_empty(self) -> None:
        assert find_fatal_mcp_servers(None) == {}

    def test_pending_is_tolerated(self) -> None:
        """A still-starting (pending) server self-heals via ToolSearch."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "pending"},
                    {"name": "mcp-workspace", "status": "pending"},
                ],
            },
        )
        assert find_fatal_mcp_servers(msg) == {}

    def test_all_connected_returns_empty(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [{"name": "mcp-workspace", "status": "connected"}],
            },
        )
        assert find_fatal_mcp_servers(msg) == {}

    def test_failed_and_unknown_are_reported(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "failed"},
                    {"name": "mcp-workspace"},
                ],
            },
        )
        assert find_fatal_mcp_servers(msg) == {
            "mcp-tools-py": "failed",
            "mcp-workspace": "unknown",
        }

    def test_needs_auth_is_tolerated(self) -> None:
        """Unauthenticated claude.ai account connectors are optional, never fatal (#1090)."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "a", "status": "connected"},
                    {"name": "b", "status": "pending"},
                    {"name": "c", "status": "needs-auth"},
                ],
            },
        )
        assert find_fatal_mcp_servers(msg) == {}

    def test_failed_still_fatal_alongside_needs_auth(self) -> None:
        """Tolerating needs-auth must not mask genuinely failed servers."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "a", "status": "connected"},
                    {"name": "b", "status": "pending"},
                    {"name": "c", "status": "needs-auth"},
                    {"name": "d", "status": "failed"},
                ],
            },
        )
        assert find_fatal_mcp_servers(msg) == {"d": "failed"}

    def test_mixed_failed_and_pending_reports_only_failed(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "failed"},
                    {"name": "mcp-workspace", "status": "pending"},
                ],
            },
        )
        assert find_fatal_mcp_servers(msg) == {"mcp-tools-py": "failed"}


class TestFindExposedMcpTools:
    """find_exposed_mcp_tools reads the init event's ``tools`` field.

    Fixtures mirror the verified real init-event shape: a connected server
    publishes its ``mcp__*`` names into ``tools`` (non-zero count), while a
    pending/cold-starting server exposes only ``ToolSearch`` (zero count).
    """

    def test_none_system_message_returns_empty(self) -> None:
        assert find_exposed_mcp_tools(None) == []

    def test_no_tools_key_returns_empty(self) -> None:
        msg = cast(StreamMessage, {"type": "system", "subtype": "init"})
        assert find_exposed_mcp_tools(msg) == []

    def test_healthy_returns_sorted_mcp_names_only(self) -> None:
        """Connected server: ``tools`` mixes builtin + mcp names (real shape)."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "tools": [
                    "ToolSearch",
                    "mcp__mcp-tools-py__run_pytest_check",
                    "mcp__mcp-workspace__read_file",
                ],
            },
        )
        assert find_exposed_mcp_tools(msg) == [
            "mcp__mcp-tools-py__run_pytest_check",
            "mcp__mcp-workspace__read_file",
        ]

    def test_degraded_connected_but_no_tools_returns_empty(self) -> None:
        """Pending/cold-start: only ToolSearch published → zero MCP tools."""
        msg = cast(
            StreamMessage,
            {"type": "system", "subtype": "init", "tools": ["ToolSearch"]},
        )
        assert find_exposed_mcp_tools(msg) == []

    def test_empty_tools_list_returns_empty(self) -> None:
        msg = cast(StreamMessage, {"type": "system", "subtype": "init", "tools": []})
        assert find_exposed_mcp_tools(msg) == []

    def test_dict_shaped_entries_are_supported(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "tools": [{"name": "mcp__x__y"}, {"name": "Bash"}],
            },
        )
        assert find_exposed_mcp_tools(msg) == ["mcp__x__y"]

    def test_duplicates_collapse_and_output_is_sorted(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "tools": [
                    "mcp__b__two",
                    "mcp__a__one",
                    "mcp__b__two",
                ],
            },
        )
        assert find_exposed_mcp_tools(msg) == ["mcp__a__one", "mcp__b__two"]


class TestLoadMcpServerNames:
    """load_mcp_server_names parses the mcpServers keys of an mcp-config file."""

    def test_happy_path_returns_server_names(self, tmp_path: Path) -> None:
        config = tmp_path / "mcp.json"
        config.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "mcp-tools-py": {"command": "x"},
                        "mcp-workspace": {"command": "y"},
                    }
                }
            ),
            encoding="utf-8",
        )
        assert load_mcp_server_names(str(config)) == {"mcp-tools-py", "mcp-workspace"}

    def test_relative_path_resolves_against_base_dir(self, tmp_path: Path) -> None:
        """A relative path resolves against base_dir (subprocess cwd), not our cwd."""
        (tmp_path / "sub").mkdir()
        config = tmp_path / "sub" / "mcp.json"
        config.write_text(
            json.dumps({"mcpServers": {"only-server": {}}}), encoding="utf-8"
        )
        result = load_mcp_server_names("sub/mcp.json", base_dir=str(tmp_path))
        assert result == {"only-server"}

    def test_missing_file_raises_value_error_naming_path(self, tmp_path: Path) -> None:
        missing = tmp_path / "nope.json"
        with pytest.raises(ValueError) as exc:
            load_mcp_server_names(str(missing))
        assert str(missing) in str(exc.value)

    def test_malformed_json_raises_value_error(self, tmp_path: Path) -> None:
        config = tmp_path / "broken.json"
        config.write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError) as exc:
            load_mcp_server_names(str(config))
        assert str(config) in str(exc.value)

    def test_top_level_non_dict_raises_value_error(self, tmp_path: Path) -> None:
        config = tmp_path / "list.json"
        config.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
        with pytest.raises(ValueError):
            load_mcp_server_names(str(config))

    def test_mcp_servers_non_dict_raises_value_error(self, tmp_path: Path) -> None:
        config = tmp_path / "bad_servers.json"
        config.write_text(json.dumps({"mcpServers": ["a", "b"]}), encoding="utf-8")
        with pytest.raises(ValueError) as exc:
            load_mcp_server_names(str(config))
        assert "mcpServers" in str(exc.value)

    def test_missing_mcp_servers_key_yields_empty_set(self, tmp_path: Path) -> None:
        """No mcpServers key is valid: a session deliberately without servers."""
        config = tmp_path / "empty.json"
        config.write_text(json.dumps({"other": 1}), encoding="utf-8")
        assert load_mcp_server_names(str(config)) == set()
