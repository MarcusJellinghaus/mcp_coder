"""Tests for the rebase prompts in ``prompts.md``.

Covers the ``Rebase Conflict Resolution`` and ``Rebase Regression Fix`` sections
used by the Python-driven rebase, including a drift check that keeps the
conflict prompt's strategy rows in sync with the packaged ``SKILL.md``, plus a
guard that the legacy ``Automated Rebase`` section stays removed.
"""

import pytest

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.data_files import find_data_file

_CONFLICT_HEADER = "Rebase Conflict Resolution"
_REGRESSION_HEADER = "Rebase Regression Fix"


def _normalize(line: str) -> str:
    """Collapse whitespace so table rows compare structurally."""
    return " ".join(line.split())


def _table_rows(lines: list[str]) -> set[str]:
    """Return normalized markdown table rows, excluding separator rows."""
    return {
        _normalize(line)
        for line in lines
        if line.strip().startswith("|") and "---" not in line
    }


def _skill_strategy_rows() -> set[str]:
    """Conflict-strategy table rows from the packaged ``SKILL.md``."""
    skill_path = find_data_file("mcp_coder", "resources/claude/skills/rebase/SKILL.md")
    skill = skill_path.read_text(encoding="utf-8")
    section: list[str] = []
    capturing = False
    for line in skill.splitlines():
        stripped = line.strip()
        if stripped.startswith("## Conflict Resolution Strategies"):
            capturing = True
            continue
        if capturing and stripped.startswith("## "):
            break
        if capturing:
            section.append(line)
    return _table_rows(section)


def _skill_llm_strategy_rows() -> set[str]:
    """SKILL.md strategy rows the LLM handles.

    The ``pr_info/`` and lockfile rows are intentionally excluded: Python
    auto-resolves ``pr_info/`` conflicts and this repo has no tracked lockfile.
    """
    return {
        row
        for row in _skill_strategy_rows()
        if row.startswith(("| Code files", "| Test files", "| Config files"))
    }


def test_automated_rebase_section_removed() -> None:
    """The legacy marker-contract prompt section is gone (Step 6)."""
    with pytest.raises(ValueError, match="Automated Rebase"):
        get_prompt(str(PROMPTS_FILE_PATH), "Automated Rebase")


def test_prompt_conflict_strategy_matches_skill() -> None:
    """The LLM-handled SKILL.md strategy rows appear in the conflict prompt."""
    prompt = get_prompt(str(PROMPTS_FILE_PATH), _CONFLICT_HEADER)
    prompt_rows = _table_rows(prompt.splitlines())
    skill_rows = _skill_llm_strategy_rows()
    assert len(skill_rows) == 3  # guard: the SKILL rows were actually located
    assert skill_rows.issubset(prompt_rows)


def test_conflict_resolution_prompt_loads() -> None:
    """Conflict prompt is retrievable, has its placeholder and the git tool."""
    prompt = get_prompt(str(PROMPTS_FILE_PATH), _CONFLICT_HEADER)
    assert prompt.strip()
    assert "[conflict_context]" in prompt
    assert "mcp__mcp-workspace__git" in prompt


def test_conflict_resolution_prompt_has_no_shell_or_markers() -> None:
    """Conflict prompt never instructs shell git or outcome markers."""
    prompt = get_prompt(str(PROMPTS_FILE_PATH), _CONFLICT_HEADER)
    assert "REBASE_OUTCOME" not in prompt
    assert "git rebase" not in prompt
    assert "Bash" not in prompt


def test_regression_fix_prompt_loads() -> None:
    """Regression prompt is retrievable, has its placeholder and the git tool."""
    prompt = get_prompt(str(PROMPTS_FILE_PATH), _REGRESSION_HEADER)
    assert prompt.strip()
    assert "[regression_output]" in prompt
    assert "mcp__mcp-workspace__git" in prompt


def test_regression_fix_prompt_rerequests_check_detail() -> None:
    """Regression prompt tells the LLM to re-run the MCP check tools for detail."""
    prompt = get_prompt(str(PROMPTS_FILE_PATH), _REGRESSION_HEADER)
    for tool in (
        "mcp__mcp-tools-py__run_pytest_check",
        "mcp__mcp-tools-py__run_pylint_check",
        "mcp__mcp-tools-py__run_mypy_check",
    ):
        assert tool in prompt


def test_regression_fix_prompt_has_no_shell_or_markers() -> None:
    """Regression prompt never instructs shell git or outcome markers."""
    prompt = get_prompt(str(PROMPTS_FILE_PATH), _REGRESSION_HEADER)
    assert "REBASE_OUTCOME" not in prompt
    assert "git rebase" not in prompt
    assert "Bash" not in prompt
