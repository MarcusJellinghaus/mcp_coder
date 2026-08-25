"""Tests for the PROMPTS section of the verify CLI orchestrator (step 16).

Split out of ``test_verify_sections_orchestration.py``, which is at the
project's file-size limit.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.prompts.prompt_loader import load_prompts

from .conftest import (
    _LC_VERIFY,
    _VERIFY,
    _claude_ok,
    _langchain_ok,
    _make_args,
    _minimal_llm_response,
    _mlflow_not_installed,
)


class TestPromptsSection:
    """PROMPTS rows: char lengths, and configured-but-missing as an error.

    ``load_prompts`` is deliberately left un-mocked and driven from a real
    ``pyproject.toml`` under ``tmp_path``, so the rows are checked against the
    same resolution a real run performs.
    """

    def _run(
        self,
        project_dir: Path,
        capsys: pytest.CaptureFixture[str],
        provider: str = "claude",
    ) -> tuple[int, str]:
        """Run execute_verify against a real ``project_dir``; return (exit, output)."""
        with (
            patch(f"{_VERIFY}.resolve_llm_method", return_value=(provider, "default")),
            patch(f"{_VERIFY}.find_claude_executable", return_value=None),
            patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok()),
            patch(f"{_LC_VERIFY}.verify_langchain", return_value=_langchain_ok()),
            patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed()),
            patch(f"{_VERIFY}.prepare_llm_environment", return_value={}),
            patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response()),
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
        ):
            result = execute_verify(_make_args(project_dir=str(project_dir)))
        return result, capsys.readouterr().out

    @staticmethod
    def _row(output: str, label: str) -> str:
        return next(line for line in output.splitlines() if label in line)

    @staticmethod
    def _write_prompts_config(project_dir: Path, body: str) -> None:
        (project_dir / "pyproject.toml").write_text(
            f"[tool.mcp-coder.prompts]\n{body}", encoding="utf-8"
        )

    def test_unconfigured_prompts_show_default_and_lengths(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 1: two ``[OK]`` rows carrying the shipped-default char counts."""
        sys_text, proj_text, _config = load_prompts(tmp_path)

        result, output = self._run(tmp_path, capsys)

        sys_row = self._row(output, "System prompt")
        assert "[OK]" in sys_row
        assert f"(shipped default) ({len(sys_text)} chars)" in sys_row

        proj_row = self._row(output, "Project prompt")
        assert "[OK]" in proj_row
        assert f"(shipped default) ({len(proj_text)} chars)" in proj_row

        # The Claude mode row is untouched.
        assert "append" in self._row(output, "Claude mode")
        assert result == 0

    def test_configured_and_present_shows_path_and_length(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 2: a configured path that resolves keeps ``[OK]`` and gains a length."""
        (tmp_path / "prompts").mkdir()
        (tmp_path / "prompts" / "system.md").write_text(
            "custom system prompt", encoding="utf-8"
        )
        self._write_prompts_config(tmp_path, 'system-prompt = "prompts/system.md"\n')

        result, output = self._run(tmp_path, capsys)

        sys_row = self._row(output, "System prompt")
        assert "[OK]" in sys_row
        assert "prompts/system.md (20 chars)" in sys_row
        assert result == 0

    def test_configured_but_missing_is_an_error_row_and_exits_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 3: the path was never used, so it must not be shown as ``[OK]``."""
        self._write_prompts_config(tmp_path, 'project-prompt = "docs/team-prompt.md"\n')

        result, output = self._run(tmp_path, capsys)

        proj_row = self._row(output, "Project prompt")
        assert "[ERR]" in proj_row
        assert (
            "docs/team-prompt.md — configured but not found; "
            "shipped default used instead" in proj_row
        )
        # No fabricated length for content that path never supplied.
        assert "chars" not in proj_row
        assert result == 1

    def test_missing_prompt_exits_1_for_langchain_too(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The new exit-1 path is provider-independent (Decision 8)."""
        self._write_prompts_config(tmp_path, 'system-prompt = "prompts/gone.md"\n')

        result, output = self._run(tmp_path, capsys, provider="langchain")

        assert "[ERR]" in self._row(output, "System prompt")
        assert result == 1

    def test_claude_md_redundancy_warning_still_shown(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TDD 5: the claude-only redundancy warning is untouched by the new rows."""
        (tmp_path / "CLAUDE.md").write_text("project rules", encoding="utf-8")
        self._write_prompts_config(tmp_path, 'project-prompt = "CLAUDE.md"\n')

        result, output = self._run(tmp_path, capsys)

        proj_row = self._row(output, "Project prompt")
        assert "[OK]" in proj_row
        assert "CLAUDE.md (13 chars)" in proj_row

        redundancy_row = self._row(output, "Redundancy")
        assert "[WARN]" in redundancy_row
        assert "will skip for Claude" in redundancy_row
        assert result == 0
