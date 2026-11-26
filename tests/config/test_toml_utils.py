"""Tests for mcp_coder.config.toml_utils."""

import logging
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.config.toml_utils import (
    TomlReadError,
    find_mcp_coder_table_lenient,
    mcp_coder_section,
)

_LOGGER = "mcp_coder.config.toml_utils"


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


class TestMcpCoderSection:
    """mcp_coder_section walks tool -> mcp-coder (-> table) with type checks."""

    @pytest.mark.parametrize(
        ("data", "table"),
        [
            ({}, None),
            ({}, "install"),
            ({"tool": {}}, None),
            ({"tool": {"other": 1}}, "install"),
            ({"tool": {"mcp-coder": {}}}, "install"),
            ({"tool": {"mcp-coder": {"extras": "dev"}}}, "install"),
        ],
    )
    def test_missing_level_is_empty(
        self, data: dict[str, Any], table: str | None
    ) -> None:
        assert mcp_coder_section(data, "pyproject.toml", table) == {}

    def test_returns_mcp_coder_table_without_table_arg(self) -> None:
        data = {"tool": {"mcp-coder": {"format_code": False}}}
        assert mcp_coder_section(data, "pyproject.toml") == {"format_code": False}

    def test_returns_valid_table(self) -> None:
        data = {"tool": {"mcp-coder": {"install": {"extras": "dev"}}}}
        assert mcp_coder_section(data, "pyproject.toml", "install") == {"extras": "dev"}

    @pytest.mark.parametrize(
        ("data", "table", "key"),
        [
            ({"tool": 1}, None, "tool"),
            ({"tool": {"mcp-coder": 1}}, None, "mcp-coder"),
            ({"tool": {"mcp-coder": {"install": "x"}}}, "install", "install"),
        ],
    )
    def test_non_table_level_raises_value_error(
        self, data: dict[str, Any], table: str | None, key: str
    ) -> None:
        label = "/some/dir/pyproject.toml"
        with pytest.raises(ValueError) as exc_info:
            mcp_coder_section(data, label, table)
        assert not isinstance(exc_info.value, TomlReadError)
        message = str(exc_info.value)
        assert label in message
        assert f"'{key}'" in message
        assert "expected a table" in message


class TestFindMcpCoderTableLenient:
    """find_mcp_coder_table_lenient returns None and warns instead of raising."""

    def test_no_files_is_none(self, tmp_path: Path) -> None:
        assert find_mcp_coder_table_lenient(tmp_path, "format_code") is None

    def test_key_absent_is_none(self, tmp_path: Path) -> None:
        _write(tmp_path / "pyproject.toml", "[tool.mcp-coder]\nother = 1\n")
        assert find_mcp_coder_table_lenient(tmp_path, "format_code") is None

    def test_pyproject_only(self, tmp_path: Path) -> None:
        _write(tmp_path / "pyproject.toml", "[tool.mcp-coder]\nformat_code = false\n")
        assert find_mcp_coder_table_lenient(tmp_path, "format_code") == (
            "pyproject.toml",
            False,
        )

    def test_mcp_coder_toml_only(self, tmp_path: Path) -> None:
        _write(tmp_path / "mcp-coder.toml", "[tool.mcp-coder]\nformat_code = true\n")
        assert find_mcp_coder_table_lenient(tmp_path, "format_code") == (
            "mcp-coder.toml",
            True,
        )

    def test_both_files_is_none_and_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _write(tmp_path / "pyproject.toml", "[tool.mcp-coder]\nformat_code = true\n")
        _write(tmp_path / "mcp-coder.toml", "[tool.mcp-coder]\nformat_code = true\n")
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            assert find_mcp_coder_table_lenient(tmp_path, "format_code") is None
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        message = warnings[0].getMessage()
        assert "pyproject.toml" in message
        assert "mcp-coder.toml" in message

    def test_malformed_mcp_coder_toml_is_none_and_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _write(tmp_path / "mcp-coder.toml", "this is not valid toml {{{")
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            assert find_mcp_coder_table_lenient(tmp_path, "format_code") is None
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "mcp-coder.toml" in warnings[0].getMessage()

    def test_non_table_tool_is_none_and_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _write(tmp_path / "pyproject.toml", "tool = 1\n")
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            assert find_mcp_coder_table_lenient(tmp_path, "format_code") is None
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "'tool'" in warnings[0].getMessage()
