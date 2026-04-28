"""Tests for _format_section and _format_mcp_section output formatting (Decision 10)."""

from typing import Any

import pytest

from mcp_coder.cli.commands.verify import (
    _LABEL_WIDTH,
    _MARKER_SLOT_WIDTH,
    _VALUE_COLUMN_INDENT,
    _collect_install_hints,
    _format_claude_mcp_section,
    _format_mcp_section,
    _format_row,
    _format_row_prefix,
    _format_section,
    _pad,
)
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus


class TestPadHeader:
    """Tests for the _pad(title) header padding helper."""

    def test_short_title_padded_to_75(self) -> None:
        out = _pad("CONFIG")
        assert out == "\n=== CONFIG " + "=" * (75 - len("=== CONFIG "))
        assert len(out.lstrip("\n")) == 75

    def test_exact_75_title_no_extra_padding(self) -> None:
        title = "X" * (75 - len("===  "))  # prefix "=== X...X " == 75
        out = _pad(title)
        assert len(out.lstrip("\n")) == 75

    def test_long_title_not_truncated(self) -> None:
        long = "MCP SERVERS (via langchain-mcp-adapters \u2014 for completeness)"
        out = _pad(long)
        assert long in out
        assert out.lstrip("\n").startswith(f"=== {long} ")


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
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        assert _format_row("Claude CLI Found", "[OK]", "YES", indent=2) in output

    def test_failed_entry_formatted_with_failure_symbol(self) -> None:
        """Entries with ok=False show [ERR] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": False, "value": "NO"},
            "overall_ok": False,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        assert _format_row("Claude CLI Found", "[ERR]", "NO", indent=2) in output

    def test_skipped_entry_formatted(self) -> None:
        """Entries with ok=None show warning indicator."""
        result: dict[str, Any] = {
            "test_prompt": {"ok": None, "value": "skipped (no API key)", "error": None},
            "overall_ok": True,
        }
        output = _format_section("TEST", result, self._symbols())
        assert "[WARN]" in output
        assert "skipped (no API key)" in output

    def test_error_shown_on_failure(self) -> None:
        """Error message appended when ok=False and error is present."""
        result: dict[str, Any] = {
            "api_integration": {"ok": False, "value": "FAILED", "error": "not found"},
            "overall_ok": False,
        }
        output = _format_section("TEST", result, self._symbols())
        assert (
            _format_row("API Integration", "[ERR]", "FAILED (not found)", indent=2)
            in output
        )

    def test_section_title_in_header(self) -> None:
        """Section header contains the title."""
        result: dict[str, Any] = {"overall_ok": True}
        output = _format_section("MY SECTION", result, self._symbols())
        assert "=== MY SECTION " in output

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
        assert (
            _format_row("Backend package", "[ERR]", "not installed", indent=2) in output
        )
        # Continuation line aligned under value column
        expected_hint_line = (
            f"{' ' * _VALUE_COLUMN_INDENT}-> pip install langchain-openai"
        )
        assert expected_hint_line in output


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
        assert "[WARN]" in output

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
        """Server names use {name:<20s} alignment."""
        statuses = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]
        output = _format_claude_mcp_section(statuses, self._symbols())
        # Name should be padded to 20 chars
        lines = output.split("\n")
        server_line = [l for l in lines if "mcp-tools-py" in l][0]
        # "  mcp-tools-py" + padding + " [OK] Connected"
        assert "mcp-tools-py      " in server_line


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


class TestBranchProtectionNesting:
    """Tests for branch protection nested rendering in _format_section (#899)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def test_children_indented_when_parent_ok(self) -> None:
        """Children render at 4-space indent under parent when ok=True."""
        result: dict[str, Any] = {
            "branch_protection": {"ok": True, "value": "main protected"},
            "ci_checks_required": {"ok": True, "value": "8 checks configured"},
            "strict_mode": {"ok": True, "value": "enabled"},
            "force_push": {"ok": True, "value": "disabled"},
            "branch_deletion": {"ok": True, "value": "disabled"},
            "overall_ok": True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        lines = output.split("\n")
        # Parent at 2-space indent
        parent_lines = [l for l in lines if "Branch protection" in l]
        assert len(parent_lines) == 1
        assert parent_lines[0].startswith("  ")
        assert "[OK]" in parent_lines[0]
        # Children at 4-space indent
        for child_label in ("CI checks required", "Force push", "Branch deletion"):
            child_lines = [l for l in lines if child_label in l]
            assert len(child_lines) == 1, f"Expected 1 line for {child_label}"
            assert child_lines[0].startswith(
                "    "
            ), f"{child_label} should be at 4-space indent"

    def test_children_suppressed_when_parent_fails(self) -> None:
        """Only parent line appears when branch_protection ok=False."""
        result: dict[str, Any] = {
            "branch_protection": {"ok": False, "value": "main is not protected"},
            "ci_checks_required": {
                "ok": False,
                "value": "unknown",
                "error": "no protection",
            },
            "strict_mode": {
                "ok": False,
                "value": "unknown",
                "error": "no protection",
            },
            "force_push": {
                "ok": False,
                "value": "unknown",
                "error": "no protection",
            },
            "branch_deletion": {
                "ok": False,
                "value": "unknown",
                "error": "no protection",
            },
            "overall_ok": False,
        }
        output = _format_section("GITHUB", result, self._symbols())
        # Parent line present
        assert "Branch protection" in output
        # Children suppressed
        assert "CI checks required" not in output
        assert "Strict mode" not in output
        assert "Force push" not in output
        assert "Branch deletion" not in output

    def test_strict_mode_no_symbol(self) -> None:
        """strict_mode renders value only — no [OK]/[ERR]/[WARN] symbol."""
        result: dict[str, Any] = {
            "branch_protection": {"ok": True, "value": "main protected"},
            "ci_checks_required": {"ok": True, "value": "8 checks configured"},
            "strict_mode": {"ok": True, "value": "enabled"},
            "force_push": {"ok": True, "value": "disabled"},
            "branch_deletion": {"ok": True, "value": "disabled"},
            "overall_ok": True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        lines = output.split("\n")
        strict_lines = [l for l in lines if "Strict mode" in l]
        assert len(strict_lines) == 1
        strict_line = strict_lines[0]
        assert "enabled" in strict_line
        assert "[OK]" not in strict_line
        assert "[ERR]" not in strict_line
        assert "[WARN]" not in strict_line

    def test_non_github_section_unaffected(self) -> None:
        """Claude section entries remain flat at 2-space indent."""
        result: dict[str, Any] = {
            "cli_found": {"ok": True, "value": "YES"},
            "cli_version": {"ok": True, "value": "1.0.0"},
            "overall_ok": True,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        lines = output.split("\n")
        content_lines = [l for l in lines if l.strip() and not l.startswith("===")]
        for line in content_lines:
            assert line.startswith("  "), f"Expected 2-space indent: {line!r}"
            assert not line.startswith(
                "    "
            ), f"Non-GitHub entry should not be at 4-space indent: {line!r}"


class TestGitHubLabelMappings:
    """Tests for GitHub label mappings in _format_section (Step 2)."""

    _GITHUB_KEYS = (
        "token_configured",
        "authenticated_user",
        "repo_url",
        "repo_accessible",
        "branch_protection",
        "ci_checks_required",
        "strict_mode",
        "force_push",
        "branch_deletion",
        "auto_delete_branches",
    )

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def test_all_github_keys_in_label_map(self) -> None:
        """All 9 GitHub check keys exist in _LABEL_MAP."""
        from mcp_coder.cli.commands.verify import _LABEL_MAP

        for key in self._GITHUB_KEYS:
            assert key in _LABEL_MAP, f"Missing key: {key}"

    def test_format_section_renders_github_labels(self) -> None:
        """_format_section renders human-readable labels for GitHub entries."""
        result: dict[str, Any] = {
            "token_configured": {"ok": True, "value": "YES"},
            "repo_accessible": {"ok": True, "value": "owner/repo"},
            "overall_ok": True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        assert "Token configured" in output
        assert "Repo accessible" in output
        assert "[OK]" in output

    def test_format_section_github_error_entry(self) -> None:
        """Entry with ok=False renders [ERR] symbol."""
        result: dict[str, Any] = {
            "token_configured": {
                "ok": False,
                "value": "not set",
                "error": "GITHUB_TOKEN not found",
            },
            "overall_ok": False,
        }
        output = _format_section("GITHUB", result, self._symbols())
        assert "Token configured" in output
        assert "[ERR]" in output
        assert "GITHUB_TOKEN not found" in output


class TestAutoDeleteBranches:
    """Tests for auto_delete_branches rendering at top level of GITHUB section (#917)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    @pytest.mark.parametrize(
        "entry, marker, value",
        [
            ({"ok": True, "value": "enabled"}, "[OK]", "enabled"),
            ({"ok": False, "value": "disabled"}, "[ERR]", "disabled"),
            (
                {
                    "ok": False,
                    "value": "unknown",
                    "error": "repository not accessible",
                },
                "[ERR]",
                "unknown (repository not accessible)",
            ),
        ],
    )
    def test_auto_delete_branches_value_cases(
        self, entry: dict[str, Any], marker: str, value: str
    ) -> None:
        """Top-level rendering: 2-space indent, symbol from ok, value, optional error suffix."""
        result: dict[str, Any] = {
            "auto_delete_branches": entry,
            "overall_ok": entry["ok"] is True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        expected_line = _format_row("Auto-delete branches", marker, value, indent=2)
        assert expected_line in output

    def test_renders_when_branch_protection_failed(self) -> None:
        """auto_delete_branches must NOT be suppressed when branch_protection.ok=False."""
        result: dict[str, Any] = {
            "branch_protection": {"ok": False, "value": "main is not protected"},
            "auto_delete_branches": {"ok": True, "value": "enabled"},
            "overall_ok": False,
        }
        output = _format_section("GITHUB", result, self._symbols())
        assert (
            _format_row("Auto-delete branches", "[OK]", "enabled", indent=2) in output
        )


class TestFormatRowHelpers:
    """Tests for the _format_row / _format_row_prefix helpers (Step 1)."""

    def _expected_prefix(
        self, label: str, marker: str, indent: int, label_width: int = _LABEL_WIDTH
    ) -> str:
        return (
            f"{' ' * indent}"
            f"{label.ljust(label_width)} "
            f"{marker.ljust(_MARKER_SLOT_WIDTH)} "
        )

    def test_labeled_row_with_ok_marker(self) -> None:
        """Labeled row with [OK] marker aligns value at column 32."""
        out = _format_row("api_key", "[OK]", "configured", indent=2)
        expected = (
            self._expected_prefix("api_key", "[OK]", indent=2) + "configured"
        ).rstrip()
        assert out == expected
        # Value substring starts at the value column index
        expected_col = 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
        assert out.index("configured") == expected_col

    def test_labeled_row_no_marker_aligns_with_marker_row(self) -> None:
        """Empty marker is padded so value column matches marker rows."""
        with_ok = _format_row("api_key", "[OK]", "configured", indent=2)
        no_marker = _format_row("endpoint", "", "not configured", indent=2)
        assert with_ok.index("configured") == no_marker.index("not configured")

    @pytest.mark.parametrize("marker", ["[OK]", "[WARN]", "[ERR]"])
    def test_value_column_identical_across_markers(self, marker: str) -> None:
        """All markers produce the same value column position."""
        out = _format_row("label", marker, "value", indent=2)
        expected_col = 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
        assert out.index("value") == expected_col

    @pytest.mark.parametrize("marker", ["[OK]", "[WARN]", "[ERR]"])
    def test_label_less_row_aligns_at_value_column(self, marker: str) -> None:
        """Label-less rows align at the same value column as labeled rows."""
        out = _format_row("", marker, "value", indent=2)
        expected_col = 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
        assert out.index("value") == expected_col

    @pytest.mark.parametrize("marker", ["[OK]", "[WARN]", "[ERR]"])
    def test_prefix_length_invariant(self, marker: str) -> None:
        """All markers produce equal-length prefixes derived from constants."""
        prefix = _format_row_prefix("x", marker, indent=2)
        expected_len = 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
        assert len(prefix) == expected_len
        assert expected_len == _VALUE_COLUMN_INDENT

    def test_prefix_lengths_match_across_markers(self) -> None:
        """Prefix lengths are identical for [OK], [WARN], [ERR]."""
        lens = {
            len(_format_row_prefix("x", marker, indent=2))
            for marker in ("[OK]", "[WARN]", "[ERR]")
        }
        assert len(lens) == 1

    def test_format_row_is_prefix_plus_value_rstripped(self) -> None:
        """Composition contract: _format_row == (prefix + value).rstrip()."""
        prefix = _format_row_prefix("label", "[OK]", indent=2)
        out = _format_row("label", "[OK]", "value", indent=2)
        assert out == (prefix + "value").rstrip()

    def test_custom_label_width_prefix_length(self) -> None:
        """Custom label_width shifts the value column by the diff."""
        prefix = _format_row_prefix("x", "[OK]", indent=2, label_width=30)
        assert len(prefix) == 2 + 30 + 1 + _MARKER_SLOT_WIDTH + 1

    def test_custom_label_width_value_column(self) -> None:
        """_format_row honours label_width when computing the value column."""
        out = _format_row("longish label", "[OK]", "Z", indent=2, label_width=30)
        expected_col = 2 + 30 + 1 + _MARKER_SLOT_WIDTH + 1
        assert out.index("Z") == expected_col
