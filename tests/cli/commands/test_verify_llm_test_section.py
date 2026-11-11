"""Tests for the ``=== LLM TEST`` section of ``mcp-coder verify``.

The section holds the MCP edit smoke test, the test prompt, the tools-exposed
rows and the ``--debug`` hint, and streams before the test prompt runs.
"""

from typing import Any

import pytest

from mcp_coder.cli.commands.verify import execute_verify

from .conftest import _make_args, _make_verify_mocks, _minimal_llm_response


def _section_lines(output: str, start: str, end: str) -> list[str]:
    """Return the lines strictly between the *start* and *end* section headers."""
    lines = output.splitlines()
    start_idx = next(i for i, line in enumerate(lines) if line.startswith(start))
    end_idx = next(i for i, line in enumerate(lines) if line.startswith(end))
    assert start_idx < end_idx
    return lines[start_idx + 1 : end_idx]


def test_llm_test_section_holds_smoke_and_prompt_rows(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Smoke test, test prompt and tools-exposed rows sit inside LLM TEST."""
    with _make_verify_mocks():
        execute_verify(_make_args())
    output = capsys.readouterr().out

    assert "=== LLM TEST" in output
    section = "\n".join(_section_lines(output, "=== LLM TEST", "=== MLFLOW"))
    assert "MCP edit smoke test" in section
    assert "Test prompt" in section
    assert "Tools exposed to model" in section


def test_llm_test_section_without_mcp_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without ``.mcp.json`` the section opens before the test prompt alone."""
    with _make_verify_mocks() as mocks:
        mocks["resolve_mcp_config_path"].return_value = None
        execute_verify(_make_args())
    output = capsys.readouterr().out

    assert "=== LLM TEST" in output
    section = _section_lines(output, "=== LLM TEST", "=== MLFLOW")
    assert section[0].lstrip().startswith("Test prompt")
    assert "MCP edit smoke test" not in output


def test_debug_line_inside_llm_test(capsys: pytest.CaptureFixture[str]) -> None:
    """A failed test prompt keeps its FAILED row and ``--debug`` hint in LLM TEST."""
    with _make_verify_mocks() as mocks:
        mocks["prompt_llm"].side_effect = RuntimeError("x")
        execute_verify(_make_args())
    output = capsys.readouterr().out

    section = _section_lines(output, "=== LLM TEST", "=== MLFLOW")
    prompt_row = next(line for line in section if "Test prompt" in line)
    assert "FAILED" in prompt_row
    assert any("Run with --debug for detailed diagnostics." in line for line in section)


def test_sections_stream_before_test_prompt(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Earlier sections and the LLM TEST header are printed before the prompt runs."""
    seen: list[str] = []

    def _prompt(*_a: Any, **_k: Any) -> dict[str, Any]:
        seen.append(capsys.readouterr().out)
        return _minimal_llm_response()

    with _make_verify_mocks() as mocks:
        mocks["prompt_llm"].side_effect = _prompt
        execute_verify(_make_args())

    assert len(seen) == 1
    before = seen[0]
    assert "=== CONFIG" in before
    assert "=== GITHUB" in before
    assert "=== LLM PROVIDER" in before
    assert "=== MCP CONFIG" in before
    assert ".mcp.json" in before
    assert "=== LLM TEST" in before
    assert "=== MLFLOW" not in before
