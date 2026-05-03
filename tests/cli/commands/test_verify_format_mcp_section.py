"""Tests for _format_mcp_section and _format_claude_mcp_section output formatting."""

from typing import Any

from mcp_coder.cli.commands.verify import (
    _format_claude_mcp_section,
    _format_mcp_section,
)
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus


class TestFormatMcpSection:
    """Tests for _format_mcp_section tool name rendering."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[WARN]", "warning": "[??]"}

    def test_tool_names_displayed_inline(self) -> None:
        """Short tool names fit on one line."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "srv": {
                    "ok": True,
                    "value": "2 tools available",
                    "tools": 2,
                    "tool_names": [("alpha", "Alpha tool"), ("beta", "Beta tool")],
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(mcp_results, self._symbols())
        assert "2 tools: alpha, beta" in output
        assert "[OK]" in output

    def test_tool_names_wrap_at_80_columns(self) -> None:
        """Long tool name lists wrap at 80 columns with indented continuation."""
        long_names = [
            (f"very_long_tool_name_{i}", f"Description {i}") for i in range(10)
        ]
        mcp_results: dict[str, Any] = {
            "servers": {
                "mcp-tools-py": {
                    "ok": True,
                    "value": f"{len(long_names)} tools available",
                    "tools": len(long_names),
                    "tool_names": long_names,
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(mcp_results, self._symbols())
        output_lines = output.split("\n")
        # Should have more than just header + 1 line (wrapping occurred)
        content_lines = [
            l for l in output_lines if "tools:" in l or l.startswith("  " + " " * 20)
        ]
        assert len(content_lines) >= 2, f"Expected wrapping, got: {output}"
        # All content lines should be <= 80 chars
        for line in output_lines[1:]:  # skip header
            assert len(line) <= 80, f"Line too long ({len(line)}): {line!r}"

    def test_no_tool_names_falls_back_to_value(self) -> None:
        """Server without tool_names key shows value string."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "mcp-tools-py": {
                    "ok": True,
                    "value": "3 tools available",
                    "tools": 3,
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(mcp_results, self._symbols())
        assert "3 tools available" in output
        assert "[OK]" in output

    def test_failed_server_shows_value_not_tools(self) -> None:
        """Failed server with ok=False shows error value."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "broken": {
                    "ok": False,
                    "value": "connection refused",
                    "error": "ConnectionError",
                },
            },
            "overall_ok": False,
        }
        output = _format_mcp_section(mcp_results, self._symbols())
        assert "connection refused" in output
        assert "[WARN]" in output

    def test_empty_tool_names_falls_back_to_value(self) -> None:
        """Server with tool_names=[] shows value string (0 tools case)."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "mcp-tools-py": {
                    "ok": True,
                    "value": "0 tools available",
                    "tools": 0,
                    "tool_names": [],
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(mcp_results, self._symbols())
        assert "0 tools available" in output

    def test_list_mcp_tools_shows_per_tool_lines(self) -> None:
        """list_mcp_tools=True renders each tool on its own line."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "srv": {
                    "ok": True,
                    "value": "2 tools available",
                    "tools": 2,
                    "tool_names": [("alpha", "Alpha tool"), ("beta", "Beta tool")],
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(mcp_results, self._symbols(), list_mcp_tools=True)
        assert "alpha" in output
        assert "Alpha tool" in output
        assert "beta" in output
        assert "Beta tool" in output
        # Each tool should be on its own indented line
        lines = output.split("\n")
        tool_lines = [l for l in lines if "alpha" in l or "beta" in l]
        assert len(tool_lines) == 2
        for line in tool_lines:
            assert line.startswith("    ")

    def test_list_mcp_tools_global_alignment(self) -> None:
        """Tool names across servers are aligned to the longest name globally."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "srv1": {
                    "ok": True,
                    "value": "1 tools available",
                    "tools": 1,
                    "tool_names": [("ab", "Short name tool")],
                },
                "srv2": {
                    "ok": True,
                    "value": "1 tools available",
                    "tools": 1,
                    "tool_names": [("a_long_tool_name", "Long name tool")],
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(mcp_results, self._symbols(), list_mcp_tools=True)
        lines = output.split("\n")
        # Find the description start positions — they should be aligned
        desc_positions = []
        for line in lines:
            if "Short name tool" in line:
                desc_positions.append(line.index("Short name tool"))
            if "Long name tool" in line:
                desc_positions.append(line.index("Long name tool"))
        assert len(desc_positions) == 2
        assert desc_positions[0] == desc_positions[1]

    def test_list_mcp_tools_missing_description_shows_name_only(self) -> None:
        """Tools with empty description show name only, no placeholder."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "srv": {
                    "ok": True,
                    "value": "2 tools available",
                    "tools": 2,
                    "tool_names": [
                        ("tool_with_desc", "Has description"),
                        ("tool_no_desc", ""),
                    ],
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(mcp_results, self._symbols(), list_mcp_tools=True)
        lines = output.split("\n")
        no_desc_line = [l for l in lines if "tool_no_desc" in l][0]
        # Should end with the tool name (stripped), no trailing spaces or placeholder
        assert no_desc_line == no_desc_line.rstrip()
        assert "Has description" not in no_desc_line

    def test_list_mcp_tools_failed_server_shows_error(self) -> None:
        """Failed server shows error line; healthy server still lists tools."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "healthy": {
                    "ok": True,
                    "value": "1 tools available",
                    "tools": 1,
                    "tool_names": [("good_tool", "Works fine")],
                },
                "broken": {
                    "ok": False,
                    "value": "connection refused",
                    "error": "ConnectionError",
                },
            },
            "overall_ok": False,
        }
        output = _format_mcp_section(mcp_results, self._symbols(), list_mcp_tools=True)
        assert "good_tool" in output
        assert "Works fine" in output
        assert "connection refused" in output
        assert "[WARN]" in output

    def test_list_mcp_tools_false_still_shows_comma_format(self) -> None:
        """Default mode with tuple data still produces comma-separated output."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "srv": {
                    "ok": True,
                    "value": "2 tools available",
                    "tools": 2,
                    "tool_names": [("alpha", "Alpha tool"), ("beta", "Beta tool")],
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(mcp_results, self._symbols(), list_mcp_tools=False)
        assert "2 tools: alpha, beta" in output

    def test_list_mcp_tools_all_servers_failed(self) -> None:
        """All servers failed — no crash, no tool lines rendered."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "srv1": {
                    "ok": False,
                    "value": "timeout",
                    "error": "TimeoutError",
                },
                "srv2": {
                    "ok": False,
                    "value": "connection refused",
                    "error": "ConnectionError",
                },
            },
            "overall_ok": False,
        }
        output = _format_mcp_section(mcp_results, self._symbols(), list_mcp_tools=True)
        assert "timeout" in output
        assert "connection refused" in output
        # No tool detail lines (lines starting with 4 spaces of indentation for tools)
        lines = output.split("\n")
        tool_detail_lines = [
            l for l in lines if l.startswith("    ") and not l.strip().startswith("[")
        ]
        assert len(tool_detail_lines) == 0


class TestFormatClaudeMcpSection:
    """Tests for _format_claude_mcp_section output formatting."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def test_connected_servers_show_success_symbol(self) -> None:
        """Two connected servers both show [OK] Connected."""
        statuses = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
            ClaudeMCPStatus(name="mcp-workspace", status_text="Connected", ok=True),
        ]
        output = _format_claude_mcp_section(statuses, self._symbols())
        assert "mcp-tools-py" in output
        assert "mcp-workspace" in output
        assert output.count("[OK]") == 2
        assert output.count("Connected") == 2

    def test_failed_server_shows_failure_symbol(self) -> None:
        """One failed server shows [ERR] Failed to start."""
        statuses = [
            ClaudeMCPStatus(
                name="mcp-tools-py", status_text="Failed to start", ok=False
            ),
        ]
        output = _format_claude_mcp_section(statuses, self._symbols())
        assert "[ERR]" in output
        assert "Failed to start" in output

    def test_section_title_default(self) -> None:
        """Title is 'MCP SERVERS (via Claude Code)'."""
        statuses = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]
        output = _format_claude_mcp_section(statuses, self._symbols())
        assert "MCP SERVERS (via Claude Code)" in output
        assert "for completeness" not in output

    def test_section_title_for_completeness(self) -> None:
        """for_completeness=True adds 'for completeness' to title."""
        statuses = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]
        output = _format_claude_mcp_section(
            statuses, self._symbols(), for_completeness=True
        )
        assert "for completeness" in output
        assert "via Claude Code" in output

    def test_server_names_left_aligned(self) -> None:
        """Server names use _LABEL_WIDTH (22) alignment."""
        statuses = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]
        output = _format_claude_mcp_section(statuses, self._symbols())
        # Name should be padded to 22 chars
        lines = output.split("\n")
        server_line = [l for l in lines if "mcp-tools-py" in l][0]
        # "  mcp-tools-py" + padding (10 spaces) + " [OK] Connected"
        assert "mcp-tools-py          " in server_line


class TestFormatMcpSectionForCompleteness:
    """Tests for _format_mcp_section with for_completeness parameter."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[WARN]", "warning": "[??]"}

    def test_format_mcp_section_for_completeness_title(self) -> None:
        """for_completeness=True changes title to include 'for completeness'."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "srv": {
                    "ok": True,
                    "value": "2 tools available",
                    "tools": 2,
                    "tool_names": [("alpha", "Alpha tool"), ("beta", "Beta tool")],
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(
            mcp_results, self._symbols(), for_completeness=True
        )
        assert "for completeness" in output
        assert "via langchain-mcp-adapters" in output
