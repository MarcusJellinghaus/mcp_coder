"""Tests for vscodeclaude template strings."""

from mcp_coder.workflows.vscodeclaude.templates import (
    AUTOMATED_SECTION_LINUX,
    AUTOMATED_SECTION_WINDOWS,
    DISCUSSION_SECTION_WINDOWS,
    VENV_SECTION_WINDOWS,
)


def test_venv_section_installs_dev_dependencies() -> None:
    """Test that VENV_SECTION_WINDOWS installs dev dependencies.

    The dev dependencies include:
    - types: Type stubs for mypy
    - test: pytest-asyncio, pytest-xdist for running tests
    - mcp: MCP server dependencies
    - Architecture tools: import-linter, pycycle, tach, vulture

    This ensures vscodeclaude workspaces have complete development environments.
    """
    # Verify correct installation command
    assert (
        "uv sync --extra dev" in VENV_SECTION_WINDOWS
    ), "VENV_SECTION_WINDOWS should install dev dependencies with '--extra dev'"

    # Verify old behavior is removed (prevent regression)
    assert (
        "uv sync --extra types" not in VENV_SECTION_WINDOWS
    ), "VENV_SECTION_WINDOWS should not use '--extra types' (incomplete dependencies)"


def test_automated_section_no_hardcoded_llm_method() -> None:
    """Test that AUTOMATED_SECTION_WINDOWS does not hardcode --llm-method.

    The LLM method should be resolved at runtime via config/env var,
    not hardcoded in templates (issue #528).
    """
    assert (
        "--llm-method" not in AUTOMATED_SECTION_WINDOWS
    ), "AUTOMATED_SECTION_WINDOWS must not hardcode '--llm-method'"


def test_discussion_section_no_hardcoded_llm_method() -> None:
    """Test that DISCUSSION_SECTION_WINDOWS does not hardcode --llm-method.

    The LLM method should be resolved at runtime via config/env var,
    not hardcoded in templates (issue #528).
    """
    assert (
        "--llm-method" not in DISCUSSION_SECTION_WINDOWS
    ), "DISCUSSION_SECTION_WINDOWS must not hardcode '--llm-method'"


def test_linux_section_has_todo_comment() -> None:
    """Test that AUTOMATED_SECTION_LINUX has a TODO comment for review.

    Linux templates use raw `claude` CLI directly instead of mcp-coder prompt.
    A TODO comment flags this for future review (issue #528).
    """
    assert (
        "# TODO" in AUTOMATED_SECTION_LINUX
    ), "AUTOMATED_SECTION_LINUX must include a '# TODO' comment for review"
