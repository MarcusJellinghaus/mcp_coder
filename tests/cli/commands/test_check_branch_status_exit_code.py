"""Tests for the --fail-on-reviews exit-code contract and parser flag.

The exit-code helper is pure (no mocking): build small BranchStatusReports and
assert the 2 -> 1 -> 0 precedence. A second layer drives the real CLI entry
point so the helper stays wired to it. See pr_info/steps/step_2.md.
"""

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp_workspace.workflows.task_tracker import TaskTrackerStatus

from mcp_coder.checks.branch_status import BranchStatusReport, CIStatus
from mcp_coder.cli.commands.check_branch_status import (
    _exit_code,
    execute_check_branch_status,
)


def _report(
    ci_status: CIStatus,
    *,
    undeterminable: bool = False,
    blocks_merge: bool = False,
) -> BranchStatusReport:
    """Build a minimal report with the fields _exit_code reads."""
    return BranchStatusReport(
        branch_name="feature/x",
        base_branch="main",
        ci_status=ci_status,
        ci_details=None,
        rebase_needed=False,
        rebase_reason="up to date",
        tasks_status=TaskTrackerStatus.COMPLETE,
        tasks_reason="all done",
        tasks_is_blocking=False,
        current_github_label="status-implementation",
        recommendations=[],
        pr_feedback_undeterminable=undeterminable,
        pr_feedback_blocks_merge=blocks_merge,
    )


class TestExitCodeContract:
    """The 2 -> 1 -> 0 precedence table."""

    @pytest.mark.parametrize("flag", [False, True])
    def test_unavailable_is_2(self, flag: bool) -> None:
        assert _exit_code(_report(CIStatus.UNAVAILABLE), flag) == 2

    @pytest.mark.parametrize("flag", [False, True])
    def test_unknown_is_2(self, flag: bool) -> None:
        assert _exit_code(_report(CIStatus.UNKNOWN), flag) == 2

    @pytest.mark.parametrize("flag", [False, True])
    def test_failed_is_1(self, flag: bool) -> None:
        assert _exit_code(_report(CIStatus.FAILED), flag) == 1

    def test_undeterminable_reviews_gated_by_flag(self) -> None:
        report = _report(CIStatus.PASSED, undeterminable=True)
        assert _exit_code(report, False) == 0
        assert _exit_code(report, True) == 2

    def test_blocking_reviews_gated_by_flag(self) -> None:
        report = _report(CIStatus.PASSED, blocks_merge=True)
        assert _exit_code(report, False) == 0
        assert _exit_code(report, True) == 1

    def test_undeterminable_wins_over_blocking(self) -> None:
        """FAILED + undeterminable reviews + flag on -> 2 (undeterminable wins)."""
        report = _report(CIStatus.FAILED, undeterminable=True, blocks_merge=True)
        assert _exit_code(report, True) == 2

    @pytest.mark.parametrize(
        "ci_status",
        [CIStatus.PASSED, CIStatus.NOT_CONFIGURED, CIStatus.PENDING],
    )
    def test_clean_is_0(self, ci_status: CIStatus) -> None:
        assert _exit_code(_report(ci_status), False) == 0
        assert _exit_code(_report(ci_status), True) == 0

    @pytest.mark.parametrize(
        ("ci_status", "expected"),
        [
            (CIStatus.PASSED, 0),
            (CIStatus.FAILED, 1),
            (CIStatus.NOT_CONFIGURED, 0),
            (CIStatus.PENDING, 0),
            (CIStatus.UNAVAILABLE, 2),
            (CIStatus.UNKNOWN, 2),
        ],
    )
    @pytest.mark.parametrize("flag", [False, True])
    def test_ci_mapping_unchanged_after_assess_ci(
        self, ci_status: CIStatus, expected: int, flag: bool
    ) -> None:
        """Regression: every CIStatus member keeps its exit code post-refactor.

        With no review feedback set, the code is driven solely by the CI
        verdict now delegated to assess_ci(require_proven=False); PENDING and
        NOT_CONFIGURED must stay clean (0) for both flags.
        """
        assert _exit_code(_report(ci_status), flag) == expected


def _args(*, fail_on_reviews: bool) -> argparse.Namespace:
    """Minimal args namespace for the plain (no wait, no fix) CLI path."""
    return argparse.Namespace(
        project_dir="/test/project",
        ci_timeout=0,
        fix=0,
        llm_truncate=False,
        llm_method="claude",
        mcp_config=None,
        settings=None,
        execution_dir=None,
        wait_for_pr=False,
        pr_timeout=600,
        fail_on_reviews=fail_on_reviews,
    )


class TestFailOnReviewsEndToEnd:
    """The review gate reaches the process exit code via the real entry point."""

    def _run(self, report: BranchStatusReport, *, fail_on_reviews: bool) -> int:
        """Drive the real entry point with only collect_branch_status faked."""
        module = "mcp_coder.cli.commands.check_branch_status"
        with (
            patch(f"{module}.resolve_project_dir", return_value=Path("/test/project")),
            patch(f"{module}.get_current_branch_name", return_value="feature/x"),
            patch(f"{module}.collect_branch_status", return_value=report) as collect,
        ):
            code = execute_check_branch_status(_args(fail_on_reviews=fail_on_reviews))
        collect.assert_called_once()
        return code

    def test_blocking_reviews_exit_1_when_gated(self) -> None:
        report = _report(CIStatus.PASSED, blocks_merge=True)
        assert self._run(report, fail_on_reviews=True) == 1

    def test_blocking_reviews_exit_0_when_informational(self) -> None:
        report = _report(CIStatus.PASSED, blocks_merge=True)
        assert self._run(report, fail_on_reviews=False) == 0

    def test_undeterminable_reviews_exit_2_when_gated(self) -> None:
        report = _report(CIStatus.PASSED, undeterminable=True)
        assert self._run(report, fail_on_reviews=True) == 2


class TestFailOnReviewsParser:
    """Parser wiring for --fail-on-reviews."""

    def _parse(self, *cli_args: str) -> argparse.Namespace:
        from mcp_coder.cli.parsers import HelpHintArgumentParser, add_check_parsers

        parser = HelpHintArgumentParser(prog="mcp-coder")
        subparsers = parser.add_subparsers(dest="command")
        add_check_parsers(subparsers)
        return parser.parse_args(["check", "branch-status", *cli_args])

    def test_default_is_false(self) -> None:
        assert self._parse().fail_on_reviews is False

    def test_flag_sets_true(self) -> None:
        assert self._parse("--fail-on-reviews").fail_on_reviews is True
