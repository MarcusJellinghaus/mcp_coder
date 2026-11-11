"""Per-section alignment tests for verify output.

Invariant: within one ``=== `` section, every marker-bearing row shares the
marker column and the value column, at every indent (2, 4 and 6). No widths
are hard-coded — each section's columns come from its own first row.

Layer 1 — ``TestPerFormatterAlignment``: per-formatter checks on stub inputs.
Fast; no ``execute_verify`` mocking burden.

Layer 2 — ``TestExecuteVerifyAlignmentSmoke``: one end-to-end run of
``execute_verify`` via ``_make_verify_mocks`` with the real PROJECT section,
checked section by section. MCP CONFIG WARNINGS is no longer special: it is
just another section under the same invariant.
"""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands import verify_sections
from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.cli.commands.verify_formatting import (
    _format_claude_mcp_section,
    _format_mcp_section,
    _format_section,
)
from mcp_coder.cli.commands.verify_render import SectionBuilder
from mcp_coder.cli.commands.verify_sections import (
    _print_environment_section,
    _print_project_section,
)
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus

from .conftest import (
    _assert_section_aligned,
    _assert_sections_aligned,
    _make_verify_mocks,
    _render,
)


def _symbols() -> dict[str, str]:
    return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}


class TestPerFormatterAlignment:
    """Layer 1 — assert per-section column invariants on individual formatters."""

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
            pytest.param(
                {
                    "token_configured": {"ok": True, "value": "configured"},
                    "perm_contents_read": {"ok": True, "value": "granted"},
                    "perm_statuses_read": {"ok": False, "value": "missing"},
                    "overall_ok": False,
                },
                id="permissions_group",
            ),
            pytest.param(
                {
                    "mcp_coder": {"ok": True, "value": "job found"},
                    "a-very-long-repository-name-x": {
                        "ok": False,
                        "value": "job missing",
                    },
                    "overall_ok": False,
                },
                id="jenkins_jobs_long_repo_name",
            ),
        ],
    )
    def test_format_section(self, result: dict[str, Any]) -> None:
        output = _render(_format_section(result, _symbols()))
        assert _assert_section_aligned(output) > 0

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
        _title, lines = _format_mcp_section(
            mcp_results, _symbols(), list_mcp_tools=list_mcp_tools
        )
        assert _assert_section_aligned(_render(lines)) > 0

    def test_format_claude_mcp_section(self) -> None:
        statuses = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
            ClaudeMCPStatus(
                name="broken-server", status_text="Failed to start", ok=False
            ),
        ]
        _title, lines = _format_claude_mcp_section(statuses, _symbols())
        assert _assert_section_aligned(_render(lines)) > 0

    def test_print_environment_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        missing = verify_sections._ENVIRONMENT_PACKAGES[0]

        def _version(pkg: str) -> str:
            if pkg == missing:
                raise PackageNotFoundError(pkg)
            return "1.0.0"

        with patch.object(verify_sections, "version", _version):
            _print_environment_section(SectionBuilder())
        captured = capsys.readouterr().out
        assert "[ERR]" in captured
        _assert_sections_aligned(captured)

    @pytest.mark.usefixtures("toolkit_with_ruff")
    @pytest.mark.parametrize("has_pyproject", [True, False])
    def test_print_project_section(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        has_pyproject: bool,
    ) -> None:
        if has_pyproject:
            (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
        _print_project_section(tmp_path, _symbols(), SectionBuilder())
        captured = capsys.readouterr().out
        _assert_sections_aligned(captured)
        if has_pyproject:
            assert any(
                line.startswith("      ruff ") for line in captured.splitlines()
            ), captured


class TestExecuteVerifyAlignmentSmoke:
    """Layer 2 — end-to-end smoke test through ``execute_verify``."""

    @pytest.mark.usefixtures("toolkit_with_ruff")
    def test_all_tabular_rows_aligned(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "pyproject.toml").write_text("[tool.black]\n", encoding="utf-8")
        args = argparse.Namespace(
            check_models=False,
            mcp_config=None,
            settings=None,
            llm_method=None,
            project_dir=str(tmp_path),
            list_mcp_tools=False,
        )
        with (
            _make_verify_mocks(),
            patch(
                "mcp_coder.cli.commands.verify._print_project_section",
                verify_sections._print_project_section,
            ),
        ):
            execute_verify(args)
        output = capsys.readouterr().out

        _assert_sections_aligned(output)
        assert "=== LLM TEST" in output
        assert "      ruff " in output
