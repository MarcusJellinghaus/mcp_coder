"""Tests for coordinator command template constants.

This module contains pure template-string assertions over the
CREATE_PLAN_COMMAND_*, IMPLEMENT_COMMAND_*, CREATE_PR_COMMAND_*, and
DEFAULT_TEST_COMMAND* constants from the coordinator package.
"""

import re

import pytest

from mcp_coder.cli.commands.coordinator import (
    CREATE_PLAN_COMMAND_TEMPLATE,
    CREATE_PLAN_COMMAND_WINDOWS,
    CREATE_PR_COMMAND_TEMPLATE,
    CREATE_PR_COMMAND_WINDOWS,
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
    IMPLEMENT_COMMAND_TEMPLATE,
    IMPLEMENT_COMMAND_WINDOWS,
    REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
    REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
    REVIEW_PLAN_COMMAND_TEMPLATE,
    REVIEW_PLAN_COMMAND_WINDOWS,
    WORKFLOW_MAPPING,
    WORKFLOW_TEMPLATES,
)


class TestTemplateWatchdogLines:
    """Tests for watchdog set-status lines in coordinator templates."""

    # -- Exit code capture --

    def test_linux_templates_capture_exit_code(self) -> None:
        """All 3 Linux templates contain RC=$?."""
        for template in (
            CREATE_PLAN_COMMAND_TEMPLATE,
            IMPLEMENT_COMMAND_TEMPLATE,
            CREATE_PR_COMMAND_TEMPLATE,
            REVIEW_PLAN_COMMAND_TEMPLATE,
            REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
        ):
            assert "RC=$?" in template, f"Missing RC=$? in {template[:40]}"

    def test_windows_templates_capture_exit_code(self) -> None:
        """All 3 Windows templates contain set RC=%ERRORLEVEL%."""
        for template in (
            CREATE_PLAN_COMMAND_WINDOWS,
            IMPLEMENT_COMMAND_WINDOWS,
            CREATE_PR_COMMAND_WINDOWS,
            REVIEW_PLAN_COMMAND_WINDOWS,
            REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        ):
            assert (
                "set RC=%ERRORLEVEL%" in template
            ), f"Missing set RC=%ERRORLEVEL% in {template[:40]}"

    def test_linux_templates_echo_rc(self) -> None:
        """All 3 Linux templates echo RC after capturing it."""
        for template in (
            CREATE_PLAN_COMMAND_TEMPLATE,
            IMPLEMENT_COMMAND_TEMPLATE,
            CREATE_PR_COMMAND_TEMPLATE,
            REVIEW_PLAN_COMMAND_TEMPLATE,
            REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
        ):
            assert "echo RC=$RC" in template, f"Missing echo RC=$RC in {template[:40]}"

    def test_windows_templates_echo_rc(self) -> None:
        """All 3 Windows templates echo RC after capturing it."""
        for template in (
            CREATE_PLAN_COMMAND_WINDOWS,
            IMPLEMENT_COMMAND_WINDOWS,
            CREATE_PR_COMMAND_WINDOWS,
            REVIEW_PLAN_COMMAND_WINDOWS,
            REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        ):
            assert (
                "echo RC=%RC%" in template
            ), f"Missing echo RC=%RC% in {template[:40]}"

    # -- Watchdog lines --

    def test_linux_templates_have_watchdog_line(self) -> None:
        """Each Linux template has the correct set-status --from-status --force || true."""
        cases = [
            (
                CREATE_PLAN_COMMAND_TEMPLATE,
                "set-status status-03f:planning-failed "
                "--from-status status-03:planning",
            ),
            (
                IMPLEMENT_COMMAND_TEMPLATE,
                "set-status status-06f:implementing-failed "
                "--from-status status-06:implementing",
            ),
            (
                CREATE_PR_COMMAND_TEMPLATE,
                "set-status status-09f:pr-creating-failed "
                "--from-status status-09:pr-creating",
            ),
            (
                REVIEW_PLAN_COMMAND_TEMPLATE,
                "set-status status-14f:plan-review-failed "
                "--from-status status-14i:plan-reviewing",
            ),
            (
                REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
                "set-status status-17f:code-review-failed "
                "--from-status status-17i:code-reviewing",
            ),
        ]
        for template, expected_fragment in cases:
            assert expected_fragment in template
            assert "--force || true" in template

    def test_windows_templates_have_watchdog_line(self) -> None:
        """Each Windows template has the correct set-status --from-status --force."""
        cases = [
            (
                CREATE_PLAN_COMMAND_WINDOWS,
                "set-status status-03f:planning-failed "
                "--from-status status-03:planning",
            ),
            (
                IMPLEMENT_COMMAND_WINDOWS,
                "set-status status-06f:implementing-failed "
                "--from-status status-06:implementing",
            ),
            (
                CREATE_PR_COMMAND_WINDOWS,
                "set-status status-09f:pr-creating-failed "
                "--from-status status-09:pr-creating",
            ),
            (
                REVIEW_PLAN_COMMAND_WINDOWS,
                "set-status status-14f:plan-review-failed "
                "--from-status status-14i:plan-reviewing",
            ),
            (
                REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
                "set-status status-17f:code-review-failed "
                "--from-status status-17i:code-reviewing",
            ),
        ]
        for template, expected_fragment in cases:
            assert expected_fragment in template
            assert "--force" in template

    # -- Exit with captured RC --

    def test_linux_templates_exit_with_captured_rc(self) -> None:
        """All 3 Linux templates end with exit $RC."""
        for template in (
            CREATE_PLAN_COMMAND_TEMPLATE,
            IMPLEMENT_COMMAND_TEMPLATE,
            CREATE_PR_COMMAND_TEMPLATE,
            REVIEW_PLAN_COMMAND_TEMPLATE,
            REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
        ):
            assert "exit $RC" in template

    def test_windows_templates_exit_with_captured_rc(self) -> None:
        """All 3 Windows templates end with exit /b %RC%."""
        for template in (
            CREATE_PLAN_COMMAND_WINDOWS,
            IMPLEMENT_COMMAND_WINDOWS,
            CREATE_PR_COMMAND_WINDOWS,
            REVIEW_PLAN_COMMAND_WINDOWS,
            REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        ):
            assert "exit /b %RC%" in template

    # -- Issue number flag --

    def test_create_plan_templates_pass_issue_number(self) -> None:
        """Both create-plan templates include --issue {issue_number} in watchdog."""
        for template in (CREATE_PLAN_COMMAND_TEMPLATE, CREATE_PLAN_COMMAND_WINDOWS):
            assert "--issue {issue_number}" in template

    def test_implement_and_pr_templates_no_issue_flag(self) -> None:
        """Implement/create-pr watchdog lines do NOT contain --issue."""
        for template in (
            IMPLEMENT_COMMAND_TEMPLATE,
            IMPLEMENT_COMMAND_WINDOWS,
            CREATE_PR_COMMAND_TEMPLATE,
            CREATE_PR_COMMAND_WINDOWS,
            REVIEW_PLAN_COMMAND_TEMPLATE,
            REVIEW_PLAN_COMMAND_WINDOWS,
            REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
            REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        ):
            # Find the watchdog line and check it doesn't have --issue
            for line in template.splitlines():
                if "set-status" in line and "--from-status" in line:
                    assert (
                        "--issue" not in line
                    ), f"Unexpected --issue in watchdog line: {line}"

    # -- Project dir in watchdog lines --

    def test_watchdog_lines_include_project_dir(self) -> None:
        """All watchdog set-status lines must include --project-dir."""
        linux_templates = (
            CREATE_PLAN_COMMAND_TEMPLATE,
            IMPLEMENT_COMMAND_TEMPLATE,
            CREATE_PR_COMMAND_TEMPLATE,
            REVIEW_PLAN_COMMAND_TEMPLATE,
            REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
        )
        windows_templates = (
            CREATE_PLAN_COMMAND_WINDOWS,
            IMPLEMENT_COMMAND_WINDOWS,
            CREATE_PR_COMMAND_WINDOWS,
            REVIEW_PLAN_COMMAND_WINDOWS,
            REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        )
        for template in linux_templates:
            found = False
            for line in template.splitlines():
                if "set-status" in line and "--from-status" in line:
                    found = True
                    assert (
                        "--project-dir /workspace/repo" in line
                    ), f"Missing --project-dir /workspace/repo in: {line}"
            assert found, "No watchdog line found in Linux template"

        for template in windows_templates:
            found = False
            for line in template.splitlines():
                if "set-status" in line and "--from-status" in line:
                    found = True
                    assert (
                        "--project-dir %WORKSPACE%\\repo" in line
                    ), f"Missing --project-dir %WORKSPACE%\\repo in: {line}"
            assert found, "No watchdog line found in Windows template"

    # -- Placeholder resolution --

    @pytest.mark.parametrize(
        "template,kwargs",
        [
            pytest.param(
                CREATE_PLAN_COMMAND_TEMPLATE,
                {"log_level": "debug", "issue_number": "42"},
                id="create-plan-linux",
            ),
            pytest.param(
                CREATE_PLAN_COMMAND_WINDOWS,
                {"log_level": "debug", "issue_number": "42"},
                id="create-plan-windows",
            ),
            pytest.param(
                IMPLEMENT_COMMAND_TEMPLATE,
                {"log_level": "debug", "branch_name": "feat-x"},
                id="implement-linux",
            ),
            pytest.param(
                IMPLEMENT_COMMAND_WINDOWS,
                {"log_level": "debug", "branch_name": "feat-x"},
                id="implement-windows",
            ),
            pytest.param(
                CREATE_PR_COMMAND_TEMPLATE,
                {"log_level": "debug", "branch_name": "feat-x"},
                id="create-pr-linux",
            ),
            pytest.param(
                CREATE_PR_COMMAND_WINDOWS,
                {"log_level": "debug", "branch_name": "feat-x"},
                id="create-pr-windows",
            ),
            pytest.param(
                REVIEW_PLAN_COMMAND_TEMPLATE,
                {"log_level": "debug", "branch_name": "feat-x"},
                id="review-plan-linux",
            ),
            pytest.param(
                REVIEW_PLAN_COMMAND_WINDOWS,
                {"log_level": "debug", "branch_name": "feat-x"},
                id="review-plan-windows",
            ),
            pytest.param(
                REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
                {"log_level": "debug", "branch_name": "feat-x"},
                id="review-implementation-linux",
            ),
            pytest.param(
                REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
                {"log_level": "debug", "branch_name": "feat-x"},
                id="review-implementation-windows",
            ),
        ],
    )
    def test_templates_placeholders_still_resolve(
        self, template: str, kwargs: dict[str, str]
    ) -> None:
        """Each template formats without KeyError using only its declared kwargs."""
        result = template.format(**kwargs)
        # After formatting, no unresolved Python format placeholders should remain.
        assert not re.search(
            r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", result
        ), f"Unresolved placeholder in formatted template: {result!r}"

    # -- Recovery matrix comment --

    def test_recovery_matrix_comment_present(self) -> None:
        """The inline comment block is present in command_templates.py source."""
        import inspect

        from mcp_coder.cli.commands.coordinator import command_templates

        source = inspect.getsource(command_templates)
        assert "Recovery matrix" in source
        assert "Silent death" in source
        assert "Hard kill" in source


class TestLinuxTemplatesUseTypesExtra:
    """Verify Linux templates use --extra types instead of --extra dev."""

    def test_default_test_command_uses_types_extra(self) -> None:
        """DEFAULT_TEST_COMMAND should use --extra types."""
        assert "uv sync --extra types" in DEFAULT_TEST_COMMAND
        assert "uv sync --extra dev" not in DEFAULT_TEST_COMMAND

    def test_create_plan_command_uses_types_extra(self) -> None:
        """CREATE_PLAN_COMMAND_TEMPLATE should use --extra types."""
        assert "uv sync --extra types" in CREATE_PLAN_COMMAND_TEMPLATE
        assert "uv sync --extra dev" not in CREATE_PLAN_COMMAND_TEMPLATE

    def test_implement_command_uses_types_extra(self) -> None:
        """IMPLEMENT_COMMAND_TEMPLATE should use --extra types."""
        assert "uv sync --extra types" in IMPLEMENT_COMMAND_TEMPLATE
        assert "uv sync --extra dev" not in IMPLEMENT_COMMAND_TEMPLATE

    def test_create_pr_command_uses_types_extra(self) -> None:
        """CREATE_PR_COMMAND_TEMPLATE should use --extra types."""
        assert "uv sync --extra types" in CREATE_PR_COMMAND_TEMPLATE
        assert "uv sync --extra dev" not in CREATE_PR_COMMAND_TEMPLATE


class TestWindowsTemplatesInstallTypeStubs:
    """Verify Windows templates include type stub installation."""

    def test_default_test_command_windows_installs_type_stubs(self) -> None:
        """DEFAULT_TEST_COMMAND_WINDOWS should install type stubs."""
        assert "uv sync --project %WORKSPACE%" in DEFAULT_TEST_COMMAND_WINDOWS
        assert "--extra types" in DEFAULT_TEST_COMMAND_WINDOWS

    def test_create_plan_command_windows_installs_type_stubs(self) -> None:
        """CREATE_PLAN_COMMAND_WINDOWS should install type stubs."""
        assert "uv sync --project %WORKSPACE%" in CREATE_PLAN_COMMAND_WINDOWS
        assert "--extra types" in CREATE_PLAN_COMMAND_WINDOWS

    def test_implement_command_windows_installs_type_stubs(self) -> None:
        """IMPLEMENT_COMMAND_WINDOWS should install type stubs."""
        assert "uv sync --project %WORKSPACE%" in IMPLEMENT_COMMAND_WINDOWS
        assert "--extra types" in IMPLEMENT_COMMAND_WINDOWS

    def test_create_pr_command_windows_installs_type_stubs(self) -> None:
        """CREATE_PR_COMMAND_WINDOWS should install type stubs."""
        assert "uv sync --project %WORKSPACE%" in CREATE_PR_COMMAND_WINDOWS
        assert "--extra types" in CREATE_PR_COMMAND_WINDOWS


class TestWorkflowTemplates:
    """Tests for the data-driven WORKFLOW_TEMPLATES dispatch table."""

    def test_every_mapping_workflow_has_template(self) -> None:
        """Every workflow in WORKFLOW_MAPPING has a WORKFLOW_TEMPLATES entry.

        This is the structural invariant that replaces the silent-fallthrough
        failure mode: a workflow present in WORKFLOW_MAPPING but missing its
        template would raise KeyError at dispatch instead of misrouting.
        """
        mapping_workflows = {config["workflow"] for config in WORKFLOW_MAPPING.values()}
        assert mapping_workflows <= set(WORKFLOW_TEMPLATES)

    def test_templates_map_to_expected_constants(self) -> None:
        """Each WORKFLOW_TEMPLATES entry pairs the correct (linux, windows) constants."""
        assert WORKFLOW_TEMPLATES["create-plan"] == (
            CREATE_PLAN_COMMAND_TEMPLATE,
            CREATE_PLAN_COMMAND_WINDOWS,
        )
        assert WORKFLOW_TEMPLATES["implement"] == (
            IMPLEMENT_COMMAND_TEMPLATE,
            IMPLEMENT_COMMAND_WINDOWS,
        )
        assert WORKFLOW_TEMPLATES["create-pr"] == (
            CREATE_PR_COMMAND_TEMPLATE,
            CREATE_PR_COMMAND_WINDOWS,
        )
        assert WORKFLOW_TEMPLATES["review-plan"] == (
            REVIEW_PLAN_COMMAND_TEMPLATE,
            REVIEW_PLAN_COMMAND_WINDOWS,
        )
        assert WORKFLOW_TEMPLATES["review-implementation"] == (
            REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
            REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        )

    def test_all_templates_format_uniformly_with_all_kwargs(self) -> None:
        """Every WORKFLOW_TEMPLATES pair formats with all three kwargs, no KeyError.

        Locks in the invariant that the dispatch site can call
        ``tpl.format(log_level=..., issue_number=..., branch_name=...)`` uniformly
        for every workflow: review/implement/create-pr use only ``{branch_name}``,
        create-plan only ``{issue_number}``, and ``str.format`` silently ignores
        the extra kwargs.
        """
        for workflow, (linux_tpl, windows_tpl) in WORKFLOW_TEMPLATES.items():
            for tpl in (linux_tpl, windows_tpl):
                # Must not raise KeyError for any entry.
                result = tpl.format(log_level="info", issue_number=1, branch_name="x")
                assert not re.search(
                    r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", result
                ), f"Unresolved placeholder for workflow {workflow!r}"


class TestReviewTemplateVerbs:
    """Tests that the review templates carry their expected verbs and checkout."""

    def test_review_plan_templates_have_verb(self) -> None:
        """Both review-plan templates invoke the review-plan verb."""
        for template in (REVIEW_PLAN_COMMAND_TEMPLATE, REVIEW_PLAN_COMMAND_WINDOWS):
            assert "review-plan" in template

    def test_review_implementation_templates_have_verb(self) -> None:
        """Both review-implementation templates invoke the verb."""
        for template in (
            REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
            REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        ):
            assert "review-implementation" in template

    def test_review_linux_templates_checkout_branch(self) -> None:
        """Linux review templates check out the feature branch via {branch_name}."""
        for template in (
            REVIEW_PLAN_COMMAND_TEMPLATE,
            REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
        ):
            assert "git checkout {branch_name}" in template

    def test_review_templates_have_no_update_issue_labels_flag(self) -> None:
        """Review templates are config-driven: no --update-issue-labels flag."""
        for template in (
            REVIEW_PLAN_COMMAND_TEMPLATE,
            REVIEW_PLAN_COMMAND_WINDOWS,
            REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
            REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        ):
            assert "--update-issue-labels" not in template
