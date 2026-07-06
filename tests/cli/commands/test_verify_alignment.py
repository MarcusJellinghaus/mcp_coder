"""Alignment-invariant tests for verify output (Step 6).

Layer 1 — ``TestPerFormatterAlignment``: parameterized per-formatter
invariants assembled from stub inputs. Fast; no ``execute_verify``
mocking burden.

Layer 2 — ``TestExecuteVerifyAlignmentSmoke``: one end-to-end run of
``execute_verify`` via ``_make_verify_mocks`` with assertions over every
captured tabular row.

The dynamic-width MCP CONFIG WARNINGS invariant lives in
``test_verify_orchestration.py`` (per ``step_4.md``); these tests use
the default ``_LABEL_WIDTH`` and Layer 2 mocks ``_validate_mcp_config``
to ``(True, "well-formed", [])`` so the always-on MCP CONFIG validity row
renders (aligned at the standard value column) while the placeholder
WARNINGS section is excluded from the captured output.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.cli.commands.verify import (
    _print_environment_section,
    _print_project_section,
    execute_verify,
)
from mcp_coder.cli.commands.verify_formatting import (
    _format_claude_mcp_section,
    _format_mcp_section,
    _format_section,
)
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus

from .conftest import (
    _assert_value_at_column,
    _expected_value_column,
    _make_verify_mocks,
)

_GROUP_HEADER_RE = re.compile(r"^  \[[A-Za-z][A-Za-z0-9_.\-]*\]\s*$")
_NOTICE_PREFIXES = (
    "Claude CLI:",
    "(uses Claude CLI",
    "Run with --debug",
    "pip install ",
    # "MCP tools exposed to model" is a deliberately long label (26 chars) that
    # overruns the default 22-col width, like the dynamic-width MCP CONFIG
    # WARNINGS section; excluded from the default-width alignment invariant.
    "MCP tools exposed to model",
)


def _symbols() -> dict[str, str]:
    return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}


def _content_lines(output: str) -> list[str]:
    """Return tabular content lines (skip headers, group headers, off-indent, too-short).

    The length filter excludes hand-rolled freeform lines that share an
    indent with tabular rows but don't extend to the value column —
    notably the per-tool detail lines emitted by ``_format_mcp_section``
    in ``list_mcp_tools=True`` mode.
    """
    result: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        if line.startswith("=== "):
            continue
        if _GROUP_HEADER_RE.match(line):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent not in (2, 4):
            continue
        if len(line) <= _expected_value_column(indent):
            continue
        result.append(line)
    return result


def _assert_aligned_by_indent(output: str) -> None:
    """Assert each indent's value column matches ``_expected_value_column(indent)``."""
    by_indent: dict[int, list[str]] = defaultdict(list)
    for line in _content_lines(output):
        indent = len(line) - len(line.lstrip(" "))
        by_indent[indent].append(line)

    assert by_indent, f"no tabular content lines parsed from output: {output!r}"

    for indent, lines_at_indent in by_indent.items():
        expected_col = _expected_value_column(indent)
        for line in lines_at_indent:
            _assert_value_at_column(line, expected_col)


class TestPerFormatterAlignment:
    """Layer 1 — assert value-column invariants on individual formatters."""

    @pytest.mark.parametrize(
        "result",
        [
            pytest.param(
                {
                    "cli_found": {"ok": True, "value": "YES"},
                    "cli_works": {"ok": False, "value": "NO", "error": "missing"},
                    "api_integration": {
                        "ok": None,
                        "value": "skipped",
                        "error": None,
                    },
                    "overall_ok": False,
                },
                id="mixed_markers_top_level",
            ),
            pytest.param(
                {
                    "branch_protection": {"ok": True, "value": "enabled"},
                    "ci_checks_required": {"ok": True, "value": "yes"},
                    "strict_mode": {"ok": True, "value": "true"},
                    "force_push": {"ok": False, "value": "allowed"},
                    "branch_deletion": {"ok": True, "value": "blocked"},
                    "overall_ok": False,
                },
                id="branch_protection_with_strict_mode_no_marker",
            ),
        ],
    )
    def test_format_section(self, result: dict[str, Any]) -> None:
        output = _format_section("TEST", result, _symbols())
        _assert_aligned_by_indent(output)

    @pytest.mark.parametrize("list_mcp_tools", [False, True])
    def test_format_mcp_section(self, list_mcp_tools: bool) -> None:
        mcp_results: dict[str, Any] = {
            "servers": {
                "ok-server": {
                    "ok": True,
                    "value": "2 tools available",
                    "tool_names": [
                        ("alpha", "Alpha tool"),
                        ("beta", "Beta tool"),
                    ],
                },
                "broken-server": {
                    "ok": False,
                    "value": "connection refused",
                },
            },
            "overall_ok": False,
        }
        output = _format_mcp_section(
            mcp_results, _symbols(), list_mcp_tools=list_mcp_tools
        )
        _assert_aligned_by_indent(output)

    def test_format_claude_mcp_section(self) -> None:
        statuses = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
            ClaudeMCPStatus(
                name="broken-server", status_text="Failed to start", ok=False
            ),
        ]
        output = _format_claude_mcp_section(statuses, _symbols())
        _assert_aligned_by_indent(output)

    def test_print_environment_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _print_environment_section()
        captured = capsys.readouterr().out
        _assert_aligned_by_indent(captured)

    @pytest.mark.parametrize("has_pyproject", [True, False])
    def test_print_project_section(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        has_pyproject: bool,
    ) -> None:
        if has_pyproject:
            (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
        _print_project_section(tmp_path, _symbols())
        captured = capsys.readouterr().out
        _assert_aligned_by_indent(captured)


class TestExecuteVerifyAlignmentSmoke:
    """Layer 2 — end-to-end smoke test through ``execute_verify``."""

    def test_all_tabular_rows_aligned(self, capsys: pytest.CaptureFixture[str]) -> None:
        args = argparse.Namespace(
            check_models=False,
            mcp_config=None,
            settings=None,
            llm_method=None,
            project_dir=None,
            list_mcp_tools=False,
        )
        with _make_verify_mocks():
            execute_verify(args)
        output = capsys.readouterr().out

        accepted_any = False
        for line in output.split("\n"):
            if line.startswith("=== "):
                continue
            if not line:
                continue
            if _GROUP_HEADER_RE.match(line):
                continue
            stripped = line.lstrip(" ")
            if any(stripped.startswith(p) for p in _NOTICE_PREFIXES):
                continue
            indent = len(line) - len(stripped)
            if indent not in (2, 4):
                continue
            expected_col = _expected_value_column(indent)
            _assert_value_at_column(line, expected_col)
            accepted_any = True

        assert accepted_any, f"no tabular rows parsed from output: {output!r}"
