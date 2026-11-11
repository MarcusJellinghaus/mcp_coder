"""Tests for CONFIG section widening: one label width for the whole section."""

from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify

from .conftest import (
    _VERIFY,
    _assert_section_aligned,
    _assert_value_at_column,
    _make_args,
    _make_verify_mocks,
)


def _config_chunk(output: str) -> str:
    """Return the CONFIG section of ``output``, header included."""
    start = output.index("=== CONFIG ")
    end = output.index("\n=== ", start)
    return output[start:end]


def _row(chunk: str, text: str) -> str:
    return next(line for line in chunk.splitlines() if text in line)


def _run(config_result: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> str:
    with (
        _make_verify_mocks(),
        patch(f"{_VERIFY}.verify_config", return_value=config_result),
    ):
        execute_verify(_make_args())
    return _config_chunk(capsys.readouterr().out)


class TestConfigSectionWidth:
    """A long CONFIG label widens every CONFIG row, at every indent."""

    def test_long_repo_key_widens_whole_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An indent-4 key of 26 chars moves the value column to 38."""
        config_result = {
            "entries": [
                {"label": "Config file", "status": "ok", "value": "found"},
                {
                    "label": "[coordinator.repos.x]",
                    "status": "ok",
                    "value": "auto_review_implementation true",
                },
            ],
            "has_error": False,
        }

        chunk = _run(config_result, capsys)

        assert _assert_section_aligned(chunk) == 2
        _assert_value_at_column(_row(chunk, "Config file"), 38)
        _assert_value_at_column(_row(chunk, "auto_review_implementation"), 38)

    def test_retired_env_var_row_joins_config_section(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The retired-variable row widens CONFIG to value column 42."""
        monkeypatch.setenv("MCP_CODER_LLM_LANGCHAIN_ENDPOINT", "http://old")
        config_result = {
            "entries": [
                {"label": "Config file", "status": "ok", "value": "found"},
                {
                    "label": "[coordinator.repos.x]",
                    "status": "ok",
                    "value": "auto_review_implementation true",
                },
            ],
            "has_error": False,
        }

        chunk = _run(config_result, capsys)

        assert _assert_section_aligned(chunk) == 3
        for text in (
            "Config file",
            "auto_review_implementation",
            "MCP_CODER_LLM_LANGCHAIN_ENDPOINT",
        ):
            _assert_value_at_column(_row(chunk, text), 42)
