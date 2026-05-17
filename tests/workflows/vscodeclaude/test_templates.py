"""Tests for vscodeclaude template strings."""

from mcp_coder.workflows.vscodeclaude.templates import (
    AUTOMATED_RESUME_SECTION_WINDOWS,
    AUTOMATED_SECTION_WINDOWS,
    INTERACTIVE_ONLY_SECTION_WINDOWS,
    INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS,
    VENV_SECTION_WINDOWS,
)


def test_venv_section_delegates_to_install_script() -> None:
    """VENV_SECTION_WINDOWS provisions the venv via ``tools/install.py``.

    Install logic is centralized in that one script (#972 follow-up);
    the template's only job is to call it with the right flags. We
    assert on flags rather than on shell commands so this test isn't
    coupled to the installer's internal sequence.
    """
    assert "{install_script_path}" in VENV_SECTION_WINDOWS
    assert "--source local" in VENV_SECTION_WINDOWS
    assert "--extras dev" in VENV_SECTION_WINDOWS
    assert "--use-sync" in VENV_SECTION_WINDOWS
    assert "--skip-templates" in VENV_SECTION_WINDOWS
    assert "--refresh" in VENV_SECTION_WINDOWS


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


def test_venv_section_sets_uv_git_shallow() -> None:
    """Test that VENV_SECTION_WINDOWS disables shallow git clones.

    setuptools_scm relies on git tags for version resolution. uv's default
    shallow clones omit tags, causing version fallback to 0.0.0 (#817).
    """
    assert (
        "UV_GIT_SHALLOW=0" in VENV_SECTION_WINDOWS
    ), "VENV_SECTION_WINDOWS should set UV_GIT_SHALLOW=0 for setuptools_scm"


def test_venv_section_extra_flags_placeholder() -> None:
    """The template carries an `{install_env_extra_flags}` placeholder.

    workspace.py uses it to append `--skip-overrides` when the
    coordinator's `--no-install-from-github` flag is set. Format on
    a sample to make sure the placeholder is actually substituted (and
    not, say, doubled-up or missing).
    """
    sample = VENV_SECTION_WINDOWS.format(
        mcp_coder_install_path="C:\\tool",
        session_folder_path="C:\\proj",
        install_script_path="C:\\tool\\.venv\\share\\mcp-coder\\install.py",
        install_env_extra_flags=" --skip-overrides",
    )
    assert "--skip-overrides" in sample
    assert "{install_env_extra_flags}" not in sample
    assert "{install_script_path}" not in sample
