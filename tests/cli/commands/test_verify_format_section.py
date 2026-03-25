"""Tests for _format_section and _format_mcp_section output formatting (Decision 10)."""

from typing import Any

from mcp_coder.cli.commands.verify import (
    _collect_install_hints,
    _format_mcp_section,
    _format_section,
)


class TestFormatSection:
    """Tests for _format_section output formatting (Decision 10)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[NO]", "warning": "[!!]"}

    def test_ok_entry_formatted_with_success_symbol(self) -> None:
        """Entries with ok=True show [OK] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": True, "value": "YES"},
            "overall_ok": True,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        assert "Claude CLI Found     [OK] YES" in output

    def test_failed_entry_formatted_with_failure_symbol(self) -> None:
        """Entries with ok=False show [NO] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": False, "value": "NO"},
            "overall_ok": False,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        assert "Claude CLI Found     [NO] NO" in output

    def test_skipped_entry_formatted(self) -> None:
        """Entries with ok=None show warning indicator."""
        result: dict[str, Any] = {
            "test_prompt": {"ok": None, "value": "skipped (no API key)", "error": None},
            "overall_ok": True,
        }
        output = _format_section("TEST", result, self._symbols())
        assert "[!!]" in output
        assert "skipped (no API key)" in output

    def test_error_shown_on_failure(self) -> None:
        """Error message appended when ok=False and error is present."""
        result: dict[str, Any] = {
            "api_integration": {"ok": False, "value": "FAILED", "error": "not found"},
            "overall_ok": False,
        }
        output = _format_section("TEST", result, self._symbols())
        assert "[NO] FAILED (not found)" in output

    def test_section_title_in_header(self) -> None:
        """Section header contains the title."""
        result: dict[str, Any] = {"overall_ok": True}
        output = _format_section("MY SECTION", result, self._symbols())
        assert "=== MY SECTION ===" in output

    def test_install_hint_rendered_inline(self) -> None:
        """When entry has install_hint and ok=False, hint appears indented below."""
        result: dict[str, Any] = {
            "backend_package": {
                "ok": False,
                "value": "not installed",
                "install_hint": "pip install langchain-openai",
            },
            "overall_ok": False,
        }
        output = _format_section("TEST", result, self._symbols())
        assert "[NO] not installed" in output
        assert "\u2192 pip install langchain-openai" in output


class TestFormatMcpSection:
    """Tests for _format_mcp_section tool name rendering."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[!!]", "warning": "[??]"}

    def test_tool_names_displayed_inline(self) -> None:
        """Short tool names fit on one line."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "srv": {
                    "ok": True,
                    "value": "2 tools available",
                    "tools": 2,
                    "tool_names": ["alpha", "beta"],
                },
            },
            "overall_ok": True,
        }
        output = _format_mcp_section(mcp_results, self._symbols())
        assert "2 tools: alpha, beta" in output
        assert "[OK]" in output

    def test_tool_names_wrap_at_80_columns(self) -> None:
        """Long tool name lists wrap at 80 columns with indented continuation."""
        long_names = [f"very_long_tool_name_{i}" for i in range(10)]
        mcp_results: dict[str, Any] = {
            "servers": {
                "tools-py": {
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
                "tools-py": {
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
        assert "[!!]" in output

    def test_empty_tool_names_falls_back_to_value(self) -> None:
        """Server with tool_names=[] shows value string (0 tools case)."""
        mcp_results: dict[str, Any] = {
            "servers": {
                "tools-py": {
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


class TestCollectInstallHints:
    """Tests for _collect_install_hints helper."""

    def test_collects_hints_from_failed_entries(self) -> None:
        """Collects install_hint values from entries with ok=False."""
        result: dict[str, Any] = {
            "pkg_a": {"ok": False, "value": "missing", "install_hint": "pip install a"},
            "pkg_b": {"ok": False, "value": "missing", "install_hint": "pip install b"},
            "overall_ok": False,
        }
        hints = _collect_install_hints(result)
        assert hints == ["pip install a", "pip install b"]

    def test_skips_entries_without_hint(self) -> None:
        """Entries with ok=False but no install_hint key are skipped."""
        result: dict[str, Any] = {
            "pkg_a": {"ok": False, "value": "missing"},
            "overall_ok": False,
        }
        hints = _collect_install_hints(result)
        assert hints == []

    def test_skips_ok_entries(self) -> None:
        """Entries with ok=True are skipped even if install_hint is present."""
        result: dict[str, Any] = {
            "pkg_a": {
                "ok": True,
                "value": "installed",
                "install_hint": "pip install a",
            },
            "overall_ok": True,
        }
        hints = _collect_install_hints(result)
        assert hints == []

    def test_skips_non_dict_entries(self) -> None:
        """Non-dict entries (like overall_ok bool) are skipped."""
        result: dict[str, Any] = {
            "overall_ok": False,
        }
        hints = _collect_install_hints(result)
        assert hints == []
