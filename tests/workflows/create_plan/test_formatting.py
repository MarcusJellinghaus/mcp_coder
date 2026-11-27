"""Tests for create-plan's formatter pre-flight and the formatted plan commit."""

import logging
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflow_steps import commit
from mcp_coder.workflow_steps.commit import FormatterConfigError
from mcp_coder.workflows.create_plan import core, run_create_plan_workflow
from tests.github_factories import make_issue_data

_CORE = "mcp_coder.workflows.create_plan.core"


@pytest.fixture
def issue_data() -> IssueData:
    """Issue data returned by the patched check_prerequisites."""
    return make_issue_data(number=123, title="Test Issue", body="Body")


def _patch_externals(
    stack: ExitStack, issue_data: IssueData, formatter_err: str | None = None
) -> MagicMock:
    """Patch the workflow's externals and attach each mock to one parent.

    Returns:
        The parent mock whose ``mock_calls`` records the call order.
    """
    parent = MagicMock()
    return_values: dict[str, object] = {
        "is_working_directory_clean": True,
        "check_prerequisites": (True, issue_data),
        "manage_branch": "feature-branch",
        "check_formatter_config": formatter_err,
        "check_pr_info_not_exists": True,
        "create_pr_info_structure": True,
        "run_planning_prompts": (True, None),
        "validate_output_files": True,
        "commit_all_changes": {"success": True, "commit_hash": "abc123"},
        "git_push": {"success": True},
        "_handle_workflow_failure": None,
    }
    for name, value in return_values.items():
        mock = stack.enter_context(patch(f"{_CORE}.{name}", return_value=value))
        parent.attach_mock(mock, name)
    return parent


def _call_names(parent: MagicMock) -> list[str]:
    """Names of the top-level calls recorded on ``parent``, in order."""
    return [call[0] for call in parent.mock_calls if "." not in call[0]]


class TestFormatterPreflight:
    """The formatter pre-flight runs between manage_branch and pr_info/ setup."""

    def test_runs_after_manage_branch_before_pr_info(
        self, issue_data: IssueData, tmp_path: Path
    ) -> None:
        """The pre-flight sits after manage_branch, before structure and prompts."""
        with ExitStack() as stack:
            parent = _patch_externals(stack, issue_data)
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 0
        names = _call_names(parent)
        preflight = names.index("check_formatter_config")
        assert names.index("manage_branch") < preflight
        assert preflight < names.index("create_pr_info_structure")
        assert preflight < names.index("run_planning_prompts")
        parent.check_formatter_config.assert_called_once_with(
            tmp_path, warn_legacy_key=True
        )

    def test_error_fails_with_prereq_label(
        self, issue_data: IssueData, tmp_path: Path
    ) -> None:
        """A pre-flight error → exit 1, prereq label, no pr_info/ and no LLM."""
        with ExitStack() as stack:
            parent = _patch_externals(stack, issue_data, "No formatter declared")
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 1
        parent._handle_workflow_failure.assert_called_once()
        failure = parent._handle_workflow_failure.call_args.args[0]
        assert failure.category == "planning_prereq_failed"
        assert failure.stage == "Prerequisites (formatter config)"
        assert failure.message == "No formatter declared"
        parent.create_pr_info_structure.assert_not_called()
        parent.run_planning_prompts.assert_not_called()


class TestPlanCommitFormatting:
    """The plan commit is formatted, best-effort."""

    def test_formats_before_commit(
        self,
        issue_data: IssueData,
        tmp_path: Path,
        formatter_mocks: SimpleNamespace,
    ) -> None:
        """format_best_effort runs with project_dir before commit_all_changes."""
        with ExitStack() as stack:
            parent = _patch_externals(stack, issue_data)
            parent.attach_mock(formatter_mocks.format_best_effort, "format_best_effort")
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 0
        formatter_mocks.format_best_effort.assert_called_once()
        assert formatter_mocks.format_best_effort.call_args.args[0] == tmp_path
        names = _call_names(parent)
        assert names.index("format_best_effort") < names.index("commit_all_changes")

    @pytest.mark.parametrize(
        "formatter_kwargs",
        [
            {"side_effect": FormatterConfigError("bad toolkit")},
            {"return_value": False},
        ],
        ids=["raises", "returns_false"],
    )
    def test_failed_formatting_warns_and_still_commits(
        self,
        formatter_kwargs: dict[str, object],
        issue_data: IssueData,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A raising or failing formatter logs a WARNING; the commit still happens."""
        run_formatters = MagicMock(**formatter_kwargs)
        monkeypatch.setattr(core, "format_best_effort", commit.format_best_effort)
        monkeypatch.setattr(commit, "run_formatters", run_formatters)

        with ExitStack() as stack, caplog.at_level(logging.WARNING):
            parent = _patch_externals(stack, issue_data)
            result = run_create_plan_workflow(123, tmp_path, "claude")

        assert result == 0
        run_formatters.assert_called_once_with(tmp_path)
        warnings = [
            r
            for r in caplog.records
            if r.levelno == logging.WARNING
            and "Formatting failed before plan commit" in r.getMessage()
        ]
        assert len(warnings) == 1
        parent.commit_all_changes.assert_called_once()
        parent.git_push.assert_called_once()
