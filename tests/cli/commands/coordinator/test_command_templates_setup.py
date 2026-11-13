"""Tests for the ``mcp-coder setup`` step in the Linux workflow templates."""

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

SETUP_CASES = [
    pytest.param(
        IMPLEMENT_COMMAND_TEMPLATE,
        "implement",
        "status-06f:implementing-failed",
        "status-06:implementing",
        id="implement",
    ),
    pytest.param(
        FIX_CI_COMMAND_TEMPLATE,
        "fix-ci",
        "status-83:ci-fix-failed",
        "status-82:fixing-ci",
        id="fix-ci",
    ),
    pytest.param(
        FIX_CONFLICT_COMMAND_TEMPLATE,
        "fix-conflict",
        "status-73:merge-conflict-failed",
        "status-72:fixing-merge-conflict",
        id="fix-conflict",
    ),
    pytest.param(
        REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
        "review-implementation",
        "status-17f:code-review-failed",
        "status-17i:code-reviewing",
        id="review-implementation",
    ),
]


def _watchdog(failed: str, current: str) -> str:
    return (
        f"mcp-coder gh-tool set-status {failed} --from-status {current} "
        "--project-dir /workspace/repo --force || true"
    )


def _command_index(lines: list[str], command: str) -> int:
    return next(
        i
        for i, line in enumerate(lines)
        if line.startswith(f"mcp-coder --log-level {{log_level}} {command} ")
    )


@pytest.mark.parametrize("template,command,failed,current", SETUP_CASES)
class TestLinuxSetupTemplates:
    """The four project-setup Linux templates run ``mcp-coder setup``."""

    def test_setup_between_pull_and_command(
        self, template: str, command: str, failed: str, current: str
    ) -> None:
        """Setup runs after ``git pull`` and before the workflow command."""
        lines = template.splitlines()
        setup_index = lines.index(SETUP_LINE)
        assert lines.index("git pull") < setup_index
        assert setup_index < _command_index(lines, command)

    def test_failure_block_runs_watchdog_and_exits(
        self, template: str, command: str, failed: str, current: str
    ) -> None:
        """A failed setup runs the template's own watchdog, then ``exit 1``."""
        lines = template.splitlines()
        setup_index = lines.index(SETUP_LINE)
        assert lines[setup_index + 1 : setup_index + 4] == [
            _watchdog(failed, current),
            "exit 1",
            "fi",
        ]

    def test_virtual_env_after_setup(
        self, template: str, command: str, failed: str, current: str
    ) -> None:
        """``VIRTUAL_ENV`` is exported after setup and before the command."""
        lines = template.splitlines()
        venv_index = lines.index(VENV_LINE)
        assert lines.index(SETUP_LINE) < venv_index < _command_index(lines, command)

    def test_watchdog_appears_twice(
        self, template: str, command: str, failed: str, current: str
    ) -> None:
        """The watchdog runs on setup failure and after the command."""
        assert template.splitlines().count(_watchdog(failed, current)) == 2

    def test_formats(
        self, template: str, command: str, failed: str, current: str
    ) -> None:
        """The template formats with the dispatch site's kwargs."""
        result = template.format(log_level="info", branch_name="b", issue_number=1)
        assert "git checkout b" in result
        assert f"mcp-coder --log-level info {command} " in result

    def test_new_lines_have_no_expansion_characters(
        self, template: str, command: str, failed: str, current: str
    ) -> None:
        """The setup block and venv line contain no ``$``, braces or backticks."""
        for line in (SETUP_LINE, _watchdog(failed, current), "exit 1", "fi", VENV_LINE):
            assert line in template.splitlines()
            for char in ("$", "{", "}", "`"):
                assert char not in line


def test_fix_conflict_does_not_list_plan_sessions() -> None:
    """fix-conflict keeps its archive section without plan sessions."""
    assert ".mcp-coder/create_plan_sessions" not in FIX_CONFLICT_COMMAND_TEMPLATE


@pytest.mark.parametrize(
    "template",
    [
        CREATE_PLAN_COMMAND_TEMPLATE,
        CREATE_PR_COMMAND_TEMPLATE,
        REVIEW_PLAN_COMMAND_TEMPLATE,
        CREATE_PLAN_COMMAND_WINDOWS,
        IMPLEMENT_COMMAND_WINDOWS,
        CREATE_PR_COMMAND_WINDOWS,
        REVIEW_PLAN_COMMAND_WINDOWS,
        REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        FIX_CI_COMMAND_WINDOWS,
        FIX_CONFLICT_COMMAND_WINDOWS,
        DEFAULT_TEST_COMMAND_WINDOWS,
    ],
)
def test_other_templates_do_not_run_setup(template: str) -> None:
    """Planning/PR Linux templates and all Windows templates skip setup."""
    assert "mcp-coder setup" not in template


def test_test_template_activates_venv_only_if_present() -> None:
    """The Linux test template activates ``.venv`` only when it exists."""
    lines = DEFAULT_TEST_COMMAND.splitlines()
    assert "if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi" in lines
    assert "source .venv/bin/activate" not in lines
