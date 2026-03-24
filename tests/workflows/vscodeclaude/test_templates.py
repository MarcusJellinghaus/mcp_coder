"""Tests for vscodeclaude template strings."""

from mcp_coder.workflows.vscodeclaude.templates import (
    AUTOMATED_RESUME_SECTION_WINDOWS,
    AUTOMATED_SECTION_WINDOWS,
    INTERACTIVE_ONLY_SECTION_WINDOWS,
    INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS,
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


def test_venv_section_has_uv_sync_retry_logic() -> None:
    """Test that VENV_SECTION_WINDOWS retries uv sync on failure.

    Windows file locks (antivirus, IDE indexing) can cause transient
    'Access is denied' errors during uv sync renames. A retry loop
    handles this reliably.
    """
    assert (
        "EnableDelayedExpansion" in VENV_SECTION_WINDOWS
    ), "VENV_SECTION_WINDOWS needs EnableDelayedExpansion for retry counter"
    assert (
        "retry_uv_sync" in VENV_SECTION_WINDOWS
    ), "VENV_SECTION_WINDOWS should have a retry label for uv sync"
    assert (
        "UV_RETRY" in VENV_SECTION_WINDOWS
    ), "VENV_SECTION_WINDOWS should track retry attempts"


def test_automated_section_has_llm_method_claude() -> None:
    """Test that AUTOMATED_SECTION_WINDOWS includes --llm-method claude.

    The automated phase creates a session that will be resumed by
    'claude --resume', which is Claude-specific. The upstream mcp-coder
    prompt call must explicitly use Claude (issue #542).
    """
    assert (
        "mcp-coder prompt" in AUTOMATED_SECTION_WINDOWS
    ), "AUTOMATED_SECTION_WINDOWS must contain 'mcp-coder prompt'"
    assert (
        "--llm-method claude" in AUTOMATED_SECTION_WINDOWS
    ), "AUTOMATED_SECTION_WINDOWS must include '--llm-method claude'"


def test_automated_resume_section_has_llm_method_claude() -> None:
    """Test that AUTOMATED_RESUME_SECTION_WINDOWS includes --llm-method claude.

    The automated resume phase continues a session that will be resumed by
    'claude --resume', which is Claude-specific. The upstream mcp-coder
    prompt call must explicitly use Claude (issue #542).
    """
    assert (
        "mcp-coder prompt" in AUTOMATED_RESUME_SECTION_WINDOWS
    ), "AUTOMATED_RESUME_SECTION_WINDOWS must contain 'mcp-coder prompt'"
    assert (
        "--llm-method claude" in AUTOMATED_RESUME_SECTION_WINDOWS
    ), "AUTOMATED_RESUME_SECTION_WINDOWS must include '--llm-method claude'"


def test_interactive_only_section_no_hardcoded_llm_method() -> None:
    """Test that INTERACTIVE_ONLY_SECTION_WINDOWS does not hardcode --llm-method."""
    assert (
        "--llm-method" not in INTERACTIVE_ONLY_SECTION_WINDOWS
    ), "INTERACTIVE_ONLY_SECTION_WINDOWS must not hardcode '--llm-method'"


def test_interactive_resume_section_no_hardcoded_llm_method() -> None:
    """Test that INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS does not hardcode --llm-method."""
    assert (
        "--llm-method" not in INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS
    ), "INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS must not hardcode '--llm-method'"
