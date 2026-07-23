"""Tests for the ``Automated Rebase`` prompt in ``prompts.md``.

Covers loader retrieval, the outcome-marker tokens, the baseline/no-regression
ordering cue, and a drift check that keeps the prompt's conflict-strategy table
in sync with the packaged ``SKILL.md``.
"""

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.data_files import find_data_file

_PROMPT_HEADER = "Automated Rebase"


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


def _load_prompt() -> str:
    return get_prompt(str(PROMPTS_FILE_PATH), _PROMPT_HEADER)


def test_automated_rebase_prompt_loads() -> None:
    """Prompt is retrievable and non-empty (body must be a fenced code block)."""
    prompt = _load_prompt()
    assert prompt.strip()


def test_prompt_contains_outcome_marker_tokens() -> None:
    """Prompt documents the outcome-marker contract."""
    prompt = _load_prompt()
    assert "REBASE_OUTCOME:" in prompt
    assert "REBASE_REASON:" in prompt


def test_prompt_requires_baseline_before_no_regression() -> None:
    """Prompt captures a baseline before rebasing and checks for regressions."""
    prompt = _load_prompt().lower()
    assert "baseline" in prompt
    assert "before" in prompt
    assert "regress" in prompt


def test_prompt_forbids_push() -> None:
    """Prompt tells the LLM not to push (Python owns the force-push)."""
    prompt = _load_prompt().lower()
    assert "not push" in prompt or "do not push" in prompt


def test_prompt_conflict_strategy_matches_skill() -> None:
    """Every SKILL.md conflict-strategy row appears in the prompt (no drift)."""
    prompt_rows = _table_rows(_load_prompt().splitlines())
    skill_rows = _skill_strategy_rows()
    assert skill_rows  # guard: the SKILL section was actually located
    assert skill_rows.issubset(prompt_rows)
