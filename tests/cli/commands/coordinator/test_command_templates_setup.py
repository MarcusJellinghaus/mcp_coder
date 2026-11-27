"""Tests for the ``mcp-coder setup`` step in the workflow and test templates."""

import re

import pytest

from mcp_coder.cli.commands.coordinator import (
    CREATE_PLAN_COMMAND_TEMPLATE,
    CREATE_PLAN_COMMAND_WINDOWS,
    CREATE_PR_COMMAND_TEMPLATE,
    CREATE_PR_COMMAND_WINDOWS,
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
    FIX_CI_COMMAND_TEMPLATE,
    FIX_CI_COMMAND_WINDOWS,
    FIX_CONFLICT_COMMAND_TEMPLATE,
    FIX_CONFLICT_COMMAND_WINDOWS,
    IMPLEMENT_COMMAND_TEMPLATE,
    IMPLEMENT_COMMAND_WINDOWS,
    REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
    REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
    REVIEW_PLAN_COMMAND_TEMPLATE,
    REVIEW_PLAN_COMMAND_WINDOWS,
)

SETUP_LINE = "if ! mcp-coder setup --project-dir /workspace/repo; then"
VENV_LINE = (
    "if [ -x .venv/bin/python ]; then export VIRTUAL_ENV=/workspace/repo/.venv; fi"
)


def _watchdog(failed: str, current: str, *, issue: bool = False) -> str:
    issue_part = " --issue {issue_number}" if issue else ""
    return (
        f"mcp-coder gh-tool set-status {failed} --from-status {current}{issue_part} "
        "--project-dir /workspace/repo --force || true"
    )


SETUP_CASES = [
    pytest.param(
        CREATE_PLAN_COMMAND_TEMPLATE,
        "create-plan {issue_number}",
        "main",
        _watchdog("status-03f:planning-failed", "status-03:planning", issue=True),
        id="create-plan",
    ),
    pytest.param(
        IMPLEMENT_COMMAND_TEMPLATE,
        "implement",
        "{branch_name}",
        _watchdog("status-06f:implementing-failed", "status-06:implementing"),
        id="implement",
    ),
    pytest.param(
        REVIEW_PLAN_COMMAND_TEMPLATE,
        "review-plan",
        "{branch_name}",
        _watchdog("status-14f:plan-review-failed", "status-14i:plan-reviewing"),
        id="review-plan",
    ),
    pytest.param(
        FIX_CI_COMMAND_TEMPLATE,
        "fix-ci",
        "{branch_name}",
        _watchdog("status-83:ci-fix-failed", "status-82:fixing-ci"),
        id="fix-ci",
    ),
    pytest.param(
        FIX_CONFLICT_COMMAND_TEMPLATE,
        "fix-conflict",
        "{branch_name}",
        _watchdog("status-73:merge-conflict-failed", "status-72:fixing-merge-conflict"),
        id="fix-conflict",
    ),
    pytest.param(
        REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
        "review-implementation",
        "{branch_name}",
        _watchdog("status-17f:code-review-failed", "status-17i:code-reviewing"),
        id="review-implementation",
    ),
]


def _command_index(lines: list[str], command: str) -> int:
    return next(
        i
        for i, line in enumerate(lines)
        if line.startswith(f"mcp-coder --log-level {{log_level}} {command} ")
    )


@pytest.mark.parametrize("template,command,checkout,watchdog", SETUP_CASES)
class TestLinuxSetupTemplates:
    """The six project-setup Linux templates run ``mcp-coder setup``."""

    def test_setup_between_pull_and_command(
        self, template: str, command: str, checkout: str, watchdog: str
    ) -> None:
        """Setup runs after ``git pull`` and before the workflow command."""
        lines = template.splitlines()
        setup_index = lines.index(SETUP_LINE)
        assert lines.index("git pull") < setup_index
        assert setup_index < _command_index(lines, command)

    def test_failure_block_runs_watchdog_and_exits(
        self, template: str, command: str, checkout: str, watchdog: str
    ) -> None:
        """A failed setup runs the template's own watchdog, then ``exit 1``."""
        lines = template.splitlines()
        setup_index = lines.index(SETUP_LINE)
        assert lines[setup_index + 1 : setup_index + 4] == [watchdog, "exit 1", "fi"]

    def test_virtual_env_after_setup(
        self, template: str, command: str, checkout: str, watchdog: str
    ) -> None:
        """``VIRTUAL_ENV`` is exported after setup and before the command."""
        lines = template.splitlines()
        venv_index = lines.index(VENV_LINE)
        assert lines.index(SETUP_LINE) < venv_index < _command_index(lines, command)

    def test_watchdog_appears_twice(
        self, template: str, command: str, checkout: str, watchdog: str
    ) -> None:
        """The watchdog runs on setup failure and after the command."""
        assert template.splitlines().count(watchdog) == 2

    def test_formats(
        self, template: str, command: str, checkout: str, watchdog: str
    ) -> None:
        """The template formats with the dispatch site's kwargs."""
        result = template.format(log_level="info", branch_name="b", issue_number=1)
        expected_checkout = checkout.format(branch_name="b")
        assert f"git checkout {expected_checkout}" in result.splitlines()
        assert f"mcp-coder --log-level info {command.format(issue_number=1)} " in result

    def test_new_lines_have_no_expansion_characters(
        self, template: str, command: str, checkout: str, watchdog: str
    ) -> None:
        """The setup block and venv line contain no ``$``, braces or backticks.

        The watchdog's only braces are the ``{issue_number}`` placeholder,
        which ``str.format`` fills before bash sees the script.
        """
        lines = template.splitlines()
        for line in (SETUP_LINE, "exit 1", "fi", VENV_LINE):
            assert line in lines
            for char in ("$", "{", "}", "`"):
                assert char not in line
        assert watchdog in lines
        without_placeholder = watchdog.replace("{issue_number}", "")
        for char in ("$", "{", "}", "`"):
            assert char not in without_placeholder


WIN_SETUP_LINE = r"mcp-coder setup --project-dir %WORKSPACE%\repo --refresh"
WIN_CHECK_LINE = "if %ERRORLEVEL% NEQ 0 ("
WIN_VENV_LINE = (
    r'if exist "%WORKSPACE%\repo\.venv\Scripts\python.exe" '
    r'set "VIRTUAL_ENV=%WORKSPACE%\repo\.venv"'
)


def _win_watchdog(failed: str, current: str, *, issue: bool = False) -> str:
    issue_part = " --issue {issue_number}" if issue else ""
    return (
        f"mcp-coder gh-tool set-status {failed} --from-status {current}{issue_part} "
        r"--project-dir %WORKSPACE%\repo --force"
    )


WIN_CASES = [
    pytest.param(
        CREATE_PLAN_COMMAND_WINDOWS,
        "mcp-coder --log-level {log_level} create-plan {issue_number} ",
        _win_watchdog("status-03f:planning-failed", "status-03:planning", issue=True),
        id="create-plan",
    ),
    pytest.param(
        IMPLEMENT_COMMAND_WINDOWS,
        "mcp-coder --log-level {log_level} implement ",
        _win_watchdog("status-06f:implementing-failed", "status-06:implementing"),
        id="implement",
    ),
    pytest.param(
        CREATE_PR_COMMAND_WINDOWS,
        "mcp-coder --log-level {log_level} create-pr ",
        _win_watchdog("status-09f:pr-creating-failed", "status-09:pr-creating"),
        id="create-pr",
    ),
    pytest.param(
        REVIEW_PLAN_COMMAND_WINDOWS,
        "mcp-coder --log-level {log_level} review-plan ",
        _win_watchdog("status-14f:plan-review-failed", "status-14i:plan-reviewing"),
        id="review-plan",
    ),
    pytest.param(
        REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        "mcp-coder --log-level {log_level} review-implementation ",
        _win_watchdog("status-17f:code-review-failed", "status-17i:code-reviewing"),
        id="review-implementation",
    ),
    pytest.param(
        FIX_CI_COMMAND_WINDOWS,
        "mcp-coder --log-level {log_level} fix-ci ",
        _win_watchdog("status-83:ci-fix-failed", "status-82:fixing-ci"),
        id="fix-ci",
    ),
    pytest.param(
        FIX_CONFLICT_COMMAND_WINDOWS,
        "mcp-coder --log-level {log_level} fix-conflict ",
        _win_watchdog(
            "status-73:merge-conflict-failed", "status-72:fixing-merge-conflict"
        ),
        id="fix-conflict",
    ),
    pytest.param(
        DEFAULT_TEST_COMMAND_WINDOWS,
        "echo %VIRTUAL_ENV%",
        None,
        id="test",
    ),
]


def _stripped_lines(template: str) -> list[str]:
    return [line.strip() for line in template.splitlines()]


def _anchor_index(lines: list[str], anchor: str) -> int:
    return next(i for i, line in enumerate(lines) if line.startswith(anchor))


@pytest.mark.parametrize("template,anchor,watchdog", WIN_CASES)
class TestWindowsSetupTemplates:
    """All eight Windows templates run ``mcp-coder setup --refresh``."""

    def test_no_activate_bat(
        self, template: str, anchor: str, watchdog: str | None
    ) -> None:
        """The template no longer calls ``activate.bat``."""
        assert "activate.bat" not in template

    def test_setup_before_anchor(
        self, template: str, anchor: str, watchdog: str | None
    ) -> None:
        """Setup runs before the workflow command (or the venv echo)."""
        lines = _stripped_lines(template)
        assert lines.index(WIN_SETUP_LINE) < _anchor_index(lines, anchor)

    def test_failure_block(
        self, template: str, anchor: str, watchdog: str | None
    ) -> None:
        """A failed setup runs the watchdog (workflows only), then ``exit /b 1``."""
        lines = _stripped_lines(template)
        expected = [WIN_CHECK_LINE, *([watchdog] if watchdog else []), "exit /b 1", ")"]
        setup_index = lines.index(WIN_SETUP_LINE)
        assert lines[setup_index + 1 : setup_index + 1 + len(expected)] == expected

    def test_watchdog_count(
        self, template: str, anchor: str, watchdog: str | None
    ) -> None:
        """Workflows run the watchdog twice; the test template never."""
        if watchdog:
            assert _stripped_lines(template).count(watchdog) == 2
        else:
            assert "gh-tool set-status" not in template

    def test_virtual_env_between_setup_and_anchor(
        self, template: str, anchor: str, watchdog: str | None
    ) -> None:
        """``VIRTUAL_ENV`` is set after setup and before the command."""
        lines = _stripped_lines(template)
        assert (
            lines.index(WIN_SETUP_LINE)
            < lines.index(WIN_VENV_LINE)
            < _anchor_index(lines, anchor)
        )


def test_windows_test_template_formats_with_log_level_only() -> None:
    """The Windows test template formats with ``log_level`` alone."""
    result = DEFAULT_TEST_COMMAND_WINDOWS.format(log_level="INFO")
    assert not re.search(r"\{[a-zA-Z_]\w*\}", result)


WIN_WORKFLOWS = [
    pytest.param(param.values[0], id=param.id)
    for param in WIN_CASES
    if param.id != "test"
]


@pytest.mark.parametrize("template", WIN_WORKFLOWS)
def test_windows_workflow_runs_in_repo_and_lists_sessions(template: str) -> None:
    """Windows workflows run in the repo and list all of .mcp-coder and logs."""
    lines = _stripped_lines(template)
    for line in (
        r"cd %WORKSPACE%\repo",
        "if exist .mcp-coder dir /s .mcp-coder",
        "dir logs",
    ):
        assert line in lines
    assert "VENV_BASE_DIR" not in template
    assert "create_plan_sessions" not in template


WIN_VERSION_LINES = (
    "where claude.exe",
    "call claude.exe --version",
    "where mcp-coder",
    "call mcp-coder --version",
)


@pytest.mark.parametrize("template", WIN_WORKFLOWS)
def test_windows_workflow_prints_tool_versions(template: str) -> None:
    """Windows workflows print Claude Code and mcp-coder versions before the command."""
    lines = _stripped_lines(template)
    command_index = _anchor_index(lines, "mcp-coder --log-level ")
    timeout_index = lines.index("set MCP_TIMEOUT=30000")
    for line in WIN_VERSION_LINES:
        assert timeout_index < lines.index(line) < command_index


LINUX_WORKFLOWS = [
    pytest.param(param.values[0], id=param.id) for param in SETUP_CASES
] + [pytest.param(CREATE_PR_COMMAND_TEMPLATE, id="create-pr")]


@pytest.mark.parametrize("template", LINUX_WORKFLOWS)
def test_linux_workflow_lists_sessions(template: str) -> None:
    """Linux workflows list all of .mcp-coder and logs without failing under set -e."""
    lines = template.splitlines()
    assert "ls -laR .mcp-coder || true" in lines
    assert "ls -la logs || true" in lines
    assert "create_plan_sessions" not in template


@pytest.mark.parametrize(
    "template",
    [CREATE_PR_COMMAND_TEMPLATE, DEFAULT_TEST_COMMAND],
)
def test_other_templates_do_not_run_setup(template: str) -> None:
    """The Linux create-pr and test templates skip setup."""
    assert "mcp-coder setup" not in template


def test_test_template_activates_venv_only_if_present() -> None:
    """The Linux test template activates ``.venv`` only when it exists."""
    lines = DEFAULT_TEST_COMMAND.splitlines()
    assert "if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi" in lines
    assert "source .venv/bin/activate" not in lines
