"""Tests for vscodeclaude template strings."""

from mcp_coder.workflows.vscodeclaude.templates import (
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


def test_automated_section_windows_has_llm_method_flag() -> None:
    """Test that AUTOMATED_SECTION_WINDOWS includes --llm-method claude.

    Without this flag, the template breaks when the LLM provider is not
    claude (regression test for issue #524).
    """
    assert (
        "--llm-method claude" in AUTOMATED_SECTION_WINDOWS
    ), "AUTOMATED_SECTION_WINDOWS must include '--llm-method claude'"


def test_discussion_section_windows_has_llm_method_flag() -> None:
    """Test that DISCUSSION_SECTION_WINDOWS includes --llm-method claude.

    Without this flag, the template breaks when the LLM provider is not
    claude (regression test for issue #524).
    """
    assert (
        "--llm-method claude" in DISCUSSION_SECTION_WINDOWS
    ), "DISCUSSION_SECTION_WINDOWS must include '--llm-method claude'"
