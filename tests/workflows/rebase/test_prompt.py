"""Tests for the rebase prompts in ``prompts.md``.

Covers the ``Rebase Conflict Resolution`` and ``Rebase Regression Fix`` sections
used by the Python-driven rebase, including a drift check that keeps the
conflict prompt's strategy rows in sync with the packaged ``SKILL.md``, plus a
guard that the legacy ``Automated Rebase`` section stays removed.
"""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.toolkits.command import CommandToolkit
from mcp_coder.utils.data_files import find_data_file
from mcp_coder.utils.toolkit_runner import llm_permissions
from mcp_coder.workflows.rebase import _build_regression_fix_prompt, _check_tool_texts

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
    """Regression prompt is retrievable, has its placeholders and the git tool."""
    prompt = get_prompt(str(PROMPTS_FILE_PATH), _REGRESSION_HEADER)
    assert prompt.strip()
    for placeholder in (
        "[check_tools]",
        "[pytest_marker_filter]",
        "[regression_output]",
        "[fix_text]",
        "[shell_ban]",
    ):
        assert placeholder in prompt
    assert "mcp__mcp-workspace__git" in prompt


_COMMAND_CONFIG = """\
[tool.mcp-coder.toolkit]
toolkit = "command"

[tool.mcp-coder.toolkit.command]
{extra}check.standard = [{{ argv = ["npm", "run", "lint"], name = "lint" }}]
test.standard = [{{ argv = ["npm", "test"], name = "unit" }}]
"""


def _render(permissions: list[str]) -> str:
    """Render the regression-fix prompt the way ``run_rebase_workflow`` does."""
    check_tools, shell_ban = _check_tool_texts(permissions)
    return _build_regression_fix_prompt(
        {
            "check_tools": check_tools,
            "regression_output": "test: unit",
            "fix_text": "FIX OUTPUT: 1 failed",
            "shell_ban": shell_ban,
        }
    )


def _command_project(tmp_path: Path, extra: str = "") -> Path:
    (tmp_path / "mcp-coder.toml").write_text(
        _COMMAND_CONFIG.format(extra=extra), encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def command_toolkit() -> Iterator[None]:
    """Resolve the toolkit to ``CommandToolkit`` (the autouse fixture says Python)."""
    with patch(
        "mcp_coder.utils.toolkit_runner._toolkit_class", lambda _name: CommandToolkit
    ):
        yield


def test_rendered_prompt_python_toolkit(tmp_path: Path) -> None:
    """``PythonToolkit``: the MCP check tools are named; shell stays banned."""
    prompt = _render(llm_permissions(tmp_path, "claude", "rebase"))
    for tool in (
        "mcp__mcp-tools-py__run_pytest_check",
        "mcp__mcp-tools-py__run_pylint_check",
        "mcp__mcp-tools-py__run_mypy_check",
    ):
        assert tool in prompt
    assert "no shell commands of any kind" in prompt
    assert "Bash" not in prompt


@pytest.mark.usefixtures("command_toolkit")
def test_rendered_prompt_command_toolkit_claude(tmp_path: Path) -> None:
    """``command`` under Claude: the granted commands, no shell ban."""
    perms = llm_permissions(_command_project(tmp_path), "claude", "rebase")
    prompt = _render(perms)
    assert "`npm run lint`" in prompt
    assert "`npm test`" in prompt
    assert "no shell commands" not in prompt
    assert "mcp__mcp-tools-py__" not in prompt


@pytest.mark.usefixtures("command_toolkit")
@pytest.mark.parametrize(
    ("extra", "provider"),
    [('llm_permissions = "none"\n', "claude"), ("", "copilot")],
)
def test_rendered_prompt_without_permissions(
    tmp_path: Path, extra: str, provider: str
) -> None:
    """No grants (``"none"`` or non-Claude): use the output; shell stays banned."""
    perms = llm_permissions(_command_project(tmp_path, extra), provider, "rebase")
    assert not perms
    prompt = _render(perms)
    assert "You cannot re-run the checks; use the output below." in prompt
    assert "no shell commands of any kind" in prompt


def test_rendered_prompt_inlines_fix_text_without_markers() -> None:
    """The check output is inlined; no outcome markers or shell git."""
    prompt = _render([])
    assert "FIX OUTPUT: 1 failed" in prompt
    assert "[fix_text]" not in prompt
    assert "REBASE_OUTCOME" not in prompt
    assert "git rebase" not in prompt
