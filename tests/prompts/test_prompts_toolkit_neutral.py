"""Every shipped prompt file stays toolkit-neutral (#1197).

Language details reach prompts only through toolkit slots, so no prompt file
may name Python tools or assume a Python project.
"""

import re
from pathlib import Path

import pytest

import mcp_coder.prompts

_PROMPT_FILES = sorted(Path(mcp_coder.prompts.__file__).parent.glob("*.md"))
_FORBIDDEN = ("pylint", "mypy", "pytest", "mcp__mcp-tools-py__")
_PYTHON_PROJECT = re.compile(r"python project", re.IGNORECASE)


def test_prompt_files_found() -> None:
    """The scan covers the prompt files, not an empty directory."""
    names = {path.name for path in _PROMPT_FILES}
    assert {"prompts.md", "system-prompt.md", "project-prompt.md"} <= names


@pytest.mark.parametrize("path", _PROMPT_FILES, ids=lambda p: p.name)
def test_prompt_file_is_toolkit_neutral(path: Path) -> None:
    """No Python tool names and no 'python project' in a prompt file."""
    text = path.read_text(encoding="utf-8")
    found = [word for word in _FORBIDDEN if word in text]
    assert not found, f"{path.name} mentions {found}"
    assert not _PYTHON_PROJECT.search(text), f"{path.name} says 'python project'"
