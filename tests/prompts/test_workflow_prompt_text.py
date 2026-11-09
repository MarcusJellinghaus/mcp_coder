"""Tests for the language-neutral wording and slots of the workflow prompts."""

import pytest

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.data_files import find_data_file

_SLOTTED_PROMPTS = {
    "Implementation Prompt Template using task tracker": "[check_instructions]",
    "Finalisation Prompt": "[check_instructions]",
    "CI Fix Prompt": "[check_instructions]",
    "Implementation Plan Creation": "[language_context]",
}

_TOOL_NAMES = ("pylint", "pytest", "mypy")


def _load(name: str) -> str:
    """Load a prompt section from the shipped prompts.md."""
    return get_prompt(str(PROMPTS_FILE_PATH), name)


@pytest.mark.parametrize(("prompt_name", "slot"), _SLOTTED_PROMPTS.items())
def test_slot_on_own_line(prompt_name: str, slot: str) -> None:
    """Each slotted prompt carries its slot on a line of its own."""
    lines = [line.strip() for line in _load(prompt_name).splitlines()]
    assert slot in lines


@pytest.mark.parametrize("prompt_name", _SLOTTED_PROMPTS)
def test_slotted_prompt_is_language_neutral(prompt_name: str) -> None:
    """No slotted prompt names Python tools or a Python project."""
    prompt = _load(prompt_name)
    for tool in _TOOL_NAMES:
        assert tool not in prompt
    assert "python project" not in prompt.lower()


def test_task_tracker_update_is_language_neutral() -> None:
    """The quality-check sub-task names no Python tool."""
    prompt = _load("Task Tracker Update Prompt")
    assert "- Quality checks — fix all issues" in prompt
    for tool in _TOOL_NAMES:
        assert tool not in prompt


def test_review_implementation_reviewer_is_language_neutral() -> None:
    """The reviewer is pointed at language conventions, not Python ones."""
    prompt = _load("Review Implementation Reviewer")
    assert "language conventions" in prompt
    assert "Python conventions" not in prompt


@pytest.mark.parametrize("filename", ["system-prompt.md", "project-prompt.md"])
def test_injected_prompt_is_language_neutral(filename: str) -> None:
    """The shipped system and project prompts name no Python tool."""
    prompt = find_data_file("mcp_coder.prompts", filename).read_text(encoding="utf-8")
    for word in (*_TOOL_NAMES, "mcp__mcp-tools-py__"):
        assert word not in prompt
    assert "python project" not in prompt.lower()


def test_system_prompt_has_one_check_instructions_slot() -> None:
    """The shipped system prompt carries [check_instructions] exactly once."""
    prompt = find_data_file("mcp_coder.prompts", "system-prompt.md").read_text(
        encoding="utf-8"
    )
    assert prompt.count("[check_instructions]") == 1
