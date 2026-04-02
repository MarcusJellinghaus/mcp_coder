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


def test_venv_section_path_set_before_mcp_coder_version() -> None:
    """Test that PATH is set before mcp-coder --version is called.

    The mcp-coder executable lives in MCP_CODER_VENV_PATH, so PATH must
    include that directory before the first mcp-coder invocation (issue #643).
    """
    lines = VENV_SECTION_WINDOWS.splitlines()
    path_line = next(
        i for i, line in enumerate(lines) if "PATH=%MCP_CODER_VENV_PATH%" in line
    )
    version_line = next(
        i for i, line in enumerate(lines) if "mcp-coder --version" in line
    )
    assert path_line < version_line, (
        f"PATH assignment (line {path_line}) must come before "
        f"mcp-coder --version (line {version_line})"
    )


def test_venv_section_path_set_twice() -> None:
    """Test that PATH=%MCP_CODER_VENV_PATH% appears exactly twice.

    First: before mcp-coder --version (so the executable is found).
    Second: after activate.bat (which overwrites PATH, see #651/#694).
    """
    count = VENV_SECTION_WINDOWS.count("PATH=%MCP_CODER_VENV_PATH%")
    assert (
        count == 2
    ), f"Expected exactly 2 PATH=%MCP_CODER_VENV_PATH% assignments, found {count}"


def test_venv_section_path_restored_after_activation() -> None:
    """Test that PATH is re-set after activate.bat call.

    activate.bat overwrites PATH, so MCP_CODER_VENV_PATH must be
    re-added afterwards to keep mcp-coder reachable (#694).
    """
    lines = VENV_SECTION_WINDOWS.splitlines()
    activate_lines = [i for i, line in enumerate(lines) if "activate.bat" in line]
    path_lines = [
        i for i, line in enumerate(lines) if "PATH=%MCP_CODER_VENV_PATH%" in line
    ]
    last_activate = max(activate_lines)
    last_path = max(path_lines)
    assert last_path > last_activate, (
        f"Last PATH assignment (line {last_path}) must come after "
        f"last activate.bat call (line {last_activate})"
    )


def test_venv_section_runs_editable_install() -> None:
    """Test that VENV_SECTION_WINDOWS runs editable install on every launch.

    The editable install ensures the current project code is always used
    in the session environment, even if the code changes between launches.
    """
    assert (
        "uv pip install -e . --no-deps" in VENV_SECTION_WINDOWS
    ), "VENV_SECTION_WINDOWS should run 'uv pip install -e . --no-deps'"
