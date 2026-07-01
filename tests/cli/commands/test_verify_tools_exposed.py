"""Tests for the _format_tools_exposed_section helper in verify."""

from mcp_coder.cli.commands.verify import (
    STATUS_SYMBOLS,
    _format_tools_exposed_section,
)


class TestFormatToolsExposedSection:
    """Tests for the _format_tools_exposed_section helper."""

    def test_connected_with_tools_ok(self) -> None:
        """Connected servers exposing >=1 tool -> [OK], ok True, names shown."""
        system_message = {
            "mcp_servers": [
                {"name": "mcp-tools-py", "status": "connected"},
                {"name": "mcp-workspace", "status": "connected"},
            ],
            "tools": ["mcp__tools__a", "mcp__workspace__b", "ToolSearch"],
        }
        lines, ok = _format_tools_exposed_section(system_message, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is True
        assert STATUS_SYMBOLS["success"] in text
        assert "2" in text
        assert "mcp-tools-py" in text
        assert "mcp-workspace" in text
        assert "alwaysLoad" not in text

    def test_connected_zero_tools_fail_with_hint(self) -> None:
        """Connected but 0 tools -> [ERR], ok False, alwaysLoad hint."""
        system_message = {
            "mcp_servers": [{"name": "mcp-tools-py", "status": "connected"}],
            "tools": [],
        }
        lines, ok = _format_tools_exposed_section(system_message, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is False
        assert STATUS_SYMBOLS["failure"] in text
        assert "alwaysLoad" in text

    def test_pending_server_warn(self) -> None:
        """A pending server -> [WARN], ok None, no alwaysLoad hint."""
        system_message = {
            "mcp_servers": [{"name": "mcp-tools-py", "status": "pending"}],
            "tools": [],
        }
        lines, ok = _format_tools_exposed_section(system_message, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is None
        assert STATUS_SYMBOLS["warning"] in text
        assert "alwaysLoad" not in text

    def test_failed_server_fail_generic_hint(self) -> None:
        """A failed (fatal) server -> [ERR], ok False, generic hint only."""
        system_message = {
            "mcp_servers": [{"name": "mcp-tools-py", "status": "failed"}],
            "tools": [],
        }
        lines, ok = _format_tools_exposed_section(system_message, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is False
        assert STATUS_SYMBOLS["failure"] in text
        assert "alwaysLoad" not in text
        assert "logs" in text

    def test_none_system_message_warn(self) -> None:
        """None (no init event) -> [WARN], ok None."""
        lines, ok = _format_tools_exposed_section(None, STATUS_SYMBOLS)
        text = "\n".join(lines)
        assert ok is None
        assert STATUS_SYMBOLS["warning"] in text
