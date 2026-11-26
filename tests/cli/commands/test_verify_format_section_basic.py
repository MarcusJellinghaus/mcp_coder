"""Tests for _format_section output formatting (Decision 10)."""

from typing import Any

from mcp_coder.cli.commands.verify_formatting import _format_section

from .conftest import (
    _expected_value_column,
    _format_row,
    _render,
)


class TestFormatSection:
    """Tests for _format_section output formatting (Decision 10)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def test_ok_entry_formatted_with_success_symbol(self) -> None:
        """Entries with ok=True show [OK] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": True, "value": "YES"},
            "overall_ok": True,
        }
        output = _render(_format_section(result, self._symbols()))
        assert _format_row("Claude CLI Found", "[OK]", "YES", indent=2) in output

    def test_failed_entry_formatted_with_failure_symbol(self) -> None:
        """Entries with ok=False show [ERR] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": False, "value": "NO"},
            "overall_ok": False,
        }
        output = _render(_format_section(result, self._symbols()))
        assert _format_row("Claude CLI Found", "[ERR]", "NO", indent=2) in output

    def test_skipped_entry_formatted(self) -> None:
        """Entries with ok=None show warning indicator."""
        result: dict[str, Any] = {
            "test_prompt": {"ok": None, "value": "skipped (no API key)", "error": None},
            "overall_ok": True,
        }
        output = _render(_format_section(result, self._symbols()))
        assert "[WARN]" in output
        assert "skipped (no API key)" in output

    def test_error_shown_on_failure(self) -> None:
        """Error message appended when ok=False and error is present."""
        result: dict[str, Any] = {
            "api_integration": {"ok": False, "value": "FAILED", "error": "not found"},
            "overall_ok": False,
        }
        output = _render(_format_section(result, self._symbols()))
        assert (
            _format_row("API Integration", "[ERR]", "FAILED (not found)", indent=2)
            in output
        )

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
        output = _render(_format_section(result, self._symbols()))
        assert (
            _format_row("Backend package", "[ERR]", "not installed", indent=2) in output
        )
        # Continuation line aligned under value column
        expected_hint_line = (
            f"{' ' * _expected_value_column()}-> pip install langchain-openai"
        )
        assert expected_hint_line in output
