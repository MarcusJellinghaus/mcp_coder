"""Tests for verify section helpers rendered through one SectionBuilder."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify_sections import (
    _print_project_section,
    _print_retired_env_var_warning,
)
from mcp_coder.utils.toolkit import VerifyItem
from mcp_coder.utils.verify_render import STATUS_SYMBOLS, Row, SectionBuilder

from .conftest import (
    _assert_section_aligned,
    _assert_value_at_column,
    _expected_value_column,
)

_DEFAULT_COL = _expected_value_column()  # 32


class TestSectionHelpersThroughBuilder:
    """``verify_sections`` helpers render through one builder per section."""

    def test_project_section_nested_rows_share_value_column(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "pyproject.toml").write_text("[tool.black]\n", encoding="utf-8")
        with patch(
            "mcp_coder.cli.commands.verify_toolkit_rows.verify_toolkit",
            lambda _l, _p, a: [VerifyItem("ruff", "ok")] if a == "format" else [],
        ):
            with SectionBuilder() as out:
                _print_project_section(tmp_path, STATUS_SYMBOLS, out)
        output = capsys.readouterr().out
        lines = output.splitlines()
        assert "  [Python]" not in lines
        assert _assert_section_aligned(output) >= 5
        for prefix in ("  Project config ", "  format_code ", "      ruff "):
            line = next(line for line in lines if line.startswith(prefix))
            _assert_value_at_column(line, _DEFAULT_COL)

    def test_retired_env_var_row_widens_config_section(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        old = "MCP_CODER_LLM_LANGCHAIN_ENDPOINT"
        monkeypatch.setenv(old, "https://relay.example/v1")
        out = SectionBuilder()
        out.open("CONFIG")
        out.add(Row("Config file", "[OK]", "ok"))
        _print_retired_env_var_warning(STATUS_SYMBOLS, out)
        out.close()
        lines = capsys.readouterr().out.splitlines()
        config_line = next(line for line in lines if "Config file" in line)
        retired_line = next(line for line in lines if old in line)
        col = _expected_value_column(label_width=len(old))
        assert col == 42
        for line in (config_line, retired_line):
            _assert_value_at_column(line, col)
