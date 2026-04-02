"""Tests for check_branch_status PR waiting functionality.

Tests PR discovery polling, remote tracking guard, CI pending hint,
and --wait-for-pr / --pr-timeout CLI arguments.
"""

import argparse
import logging
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.checks.branch_status import CI_PENDING, BranchStatusReport

# Test-first approach: Try to import the module, skip dependent tests if not available
try:
    from mcp_coder.cli.commands.check_branch_status import execute_check_branch_status

    CHECK_BRANCH_STATUS_MODULE_AVAILABLE = True
except ImportError:
    CHECK_BRANCH_STATUS_MODULE_AVAILABLE = False


def _make_base_args(**overrides: object) -> argparse.Namespace:
    """Create a Namespace with sensible defaults for execute_check_branch_status."""
    defaults: dict[str, object] = dict(
        project_dir="/test/project",
        ci_timeout=0,
        fix=0,
        llm_truncate=False,
        llm_method="claude",
        mcp_config=None,
        execution_dir=None,
        wait_for_pr=False,
        pr_timeout=600,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _make_report(**overrides: object) -> BranchStatusReport:
    """Create a sample BranchStatusReport with optional overrides."""
    kwargs: dict[str, object] = dict(
        branch_name="feature/test-branch",
        base_branch="main",
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Branch is up to date with main",
        tasks_complete=True,
        current_github_label="status-implementation",
        recommendations=["Ready to merge"],
    )
    kwargs.update(overrides)
    return BranchStatusReport(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestWaitForPrParserArgs:
    """Tests for --wait-for-pr and --pr-timeout CLI arguments."""

    def _parse(self, *cli_args: str) -> argparse.Namespace:
        """Parse CLI args through the real parser and return the Namespace."""
        from mcp_coder.cli.parsers import HelpHintArgumentParser, add_check_parsers

        parser = HelpHintArgumentParser(prog="mcp-coder")
        subparsers = parser.add_subparsers(dest="command")
        add_check_parsers(subparsers)
        return parser.parse_args(["check", "branch-status", *cli_args])

    def test_wait_for_pr_flag_default(self) -> None:
        args = self._parse()
        assert args.wait_for_pr is False

    def test_wait_for_pr_flag_set(self) -> None:
        args = self._parse("--wait-for-pr")
        assert args.wait_for_pr is True

    def test_pr_timeout_default(self) -> None:
        args = self._parse()
        assert args.pr_timeout == 600

    def test_pr_timeout_custom(self) -> None:
        args = self._parse("--pr-timeout", "300")
        assert args.pr_timeout == 300

    def test_pr_timeout_negative_rejected(self) -> None:
        with pytest.raises(SystemExit):
            self._parse("--pr-timeout", "-1")


# ---------------------------------------------------------------------------
# has_remote_tracking_branch helper tests
# ---------------------------------------------------------------------------


class TestHasRemoteTrackingBranch:
    """Tests for has_remote_tracking_branch utility."""

    @patch("mcp_coder.utils.git_operations.branch_queries._safe_repo_context")
    @patch("mcp_coder.utils.git_operations.branch_queries.is_git_repository")
    def test_has_remote_tracking_branch_true(
        self, mock_is_git: Mock, mock_ctx: Mock
    ) -> None:
        from mcp_coder.utils.git_operations.branch_queries import (
            has_remote_tracking_branch,
        )

        mock_is_git.return_value = True
        mock_repo = Mock()
        mock_branch = Mock()
        mock_branch.tracking_branch.return_value = Mock()  # non-None = has tracking
        mock_repo.active_branch = mock_branch
        mock_ctx.return_value.__enter__ = Mock(return_value=mock_repo)
        mock_ctx.return_value.__exit__ = Mock(return_value=False)

        assert has_remote_tracking_branch(Path("/test")) is True

    @patch("mcp_coder.utils.git_operations.branch_queries._safe_repo_context")
    @patch("mcp_coder.utils.git_operations.branch_queries.is_git_repository")
    def test_has_remote_tracking_branch_false(
        self, mock_is_git: Mock, mock_ctx: Mock
    ) -> None:
        from mcp_coder.utils.git_operations.branch_queries import (
            has_remote_tracking_branch,
        )

        mock_is_git.return_value = True
        mock_repo = Mock()
        mock_branch = Mock()
        mock_branch.tracking_branch.return_value = None  # None = no tracking
        mock_repo.active_branch = mock_branch
        mock_ctx.return_value.__enter__ = Mock(return_value=mock_repo)
        mock_ctx.return_value.__exit__ = Mock(return_value=False)

        assert has_remote_tracking_branch(Path("/test")) is False


# ---------------------------------------------------------------------------
# Remote tracking guard tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestRemoteTrackingGuard:
    """Tests for the remote tracking branch guard in PR waiting."""

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.has_remote_tracking_branch")
    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    def test_wait_for_pr_no_remote_tracking(
        self,
        mock_branch: Mock,
        mock_has_remote: Mock,
        mock_resolve: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """No upstream → exit code 2, error message."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        mock_has_remote.return_value = False

        args = _make_base_args(wait_for_pr=True)
        with caplog.at_level(logging.DEBUG):
            result = execute_check_branch_status(args)

        assert result == 2
        assert any(
            "no remote tracking branch" in r.message.lower() for r in caplog.records
        )

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.has_remote_tracking_branch")
    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.PullRequestManager")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    @patch("mcp_coder.cli.commands.check_branch_status.time")
    def test_wait_for_pr_with_remote_tracking(
        self,
        mock_time: Mock,
        mock_collect: Mock,
        mock_pr_cls: Mock,
        mock_branch: Mock,
        mock_has_remote: Mock,
        mock_resolve: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Has upstream → proceeds to polling."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        mock_has_remote.return_value = True
        mock_time.monotonic.side_effect = [0, 0, 100]  # start, check, after poll
        mock_time.sleep = Mock()

        pr_data = {"number": 42, "url": "https://github.com/org/repo/pull/42"}
        mock_pr_cls.return_value.find_pull_request_by_head.return_value = [pr_data]

        mock_collect.return_value = _make_report()

        args = _make_base_args(wait_for_pr=True, pr_timeout=600)
        result = execute_check_branch_status(args)

        assert result == 0
        mock_pr_cls.return_value.find_pull_request_by_head.assert_called_once_with(
            "feature/xyz"
        )


# ---------------------------------------------------------------------------
# PR polling tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestPRPolling:
    """Tests for PR discovery polling behaviour."""

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.has_remote_tracking_branch")
    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.PullRequestManager")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    @patch("mcp_coder.cli.commands.check_branch_status.time")
    def test_wait_for_pr_found_immediately(
        self,
        mock_time: Mock,
        mock_collect: Mock,
        mock_pr_cls: Mock,
        mock_branch: Mock,
        mock_has_remote: Mock,
        mock_resolve: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """PR exists on first poll → proceeds, report has PR fields."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        mock_has_remote.return_value = True
        mock_time.monotonic.side_effect = [0, 0, 100]
        mock_time.sleep = Mock()

        pr_data = {"number": 42, "url": "https://github.com/org/repo/pull/42"}
        mock_pr_cls.return_value.find_pull_request_by_head.return_value = [pr_data]

        base_report = _make_report()
        mock_collect.return_value = base_report

        args = _make_base_args(wait_for_pr=True)
        with caplog.at_level(logging.DEBUG):
            result = execute_check_branch_status(args)

        assert result == 0
        assert any("PR #42 found" in r.message for r in caplog.records)

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.has_remote_tracking_branch")
    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.PullRequestManager")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    @patch("mcp_coder.cli.commands.check_branch_status.time")
    def test_wait_for_pr_found_after_retries(
        self,
        mock_time: Mock,
        mock_collect: Mock,
        mock_pr_cls: Mock,
        mock_branch: Mock,
        mock_has_remote: Mock,
        mock_resolve: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """PR found on 2nd poll → correct behavior."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        mock_has_remote.return_value = True
        # monotonic: start, 1st-loop-check (before deadline), after-sleep-check (before deadline), 2nd-loop-check
        mock_time.monotonic.side_effect = [0, 0, 20, 20, 100]
        mock_time.sleep = Mock()

        pr_data = {"number": 55, "url": "https://github.com/org/repo/pull/55"}
        mock_pr_cls.return_value.find_pull_request_by_head.side_effect = [
            [],  # first poll: no PR
            [pr_data],  # second poll: found!
        ]

        mock_collect.return_value = _make_report()

        args = _make_base_args(wait_for_pr=True, pr_timeout=600)
        with caplog.at_level(logging.DEBUG):
            result = execute_check_branch_status(args)

        assert result == 0
        assert mock_pr_cls.return_value.find_pull_request_by_head.call_count == 2
        mock_time.sleep.assert_called_once_with(20)
        assert any("PR #55 found" in r.message for r in caplog.records)

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.has_remote_tracking_branch")
    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.PullRequestManager")
    @patch("mcp_coder.cli.commands.check_branch_status.time")
    def test_wait_for_pr_timeout(
        self,
        mock_time: Mock,
        mock_pr_cls: Mock,
        mock_branch: Mock,
        mock_has_remote: Mock,
        mock_resolve: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """No PR within timeout → exit code 1, timeout message."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        mock_has_remote.return_value = True
        # monotonic: start=0, while-check=0, sleep-guard=700 (past deadline), while-check=700
        mock_time.monotonic.side_effect = [0, 0, 700, 700]
        mock_time.sleep = Mock()

        mock_pr_cls.return_value.find_pull_request_by_head.return_value = []

        args = _make_base_args(wait_for_pr=True, pr_timeout=600)
        with caplog.at_level(logging.DEBUG):
            result = execute_check_branch_status(args)

        assert result == 1
        assert any("No PR found" in r.message for r in caplog.records)
        assert any("timeout" in r.message.lower() for r in caplog.records)

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.has_remote_tracking_branch")
    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.PullRequestManager")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    @patch("mcp_coder.cli.commands.check_branch_status.time")
    def test_wait_for_pr_multiple_prs_warning(
        self,
        mock_time: Mock,
        mock_collect: Mock,
        mock_pr_cls: Mock,
        mock_branch: Mock,
        mock_has_remote: Mock,
        mock_resolve: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Multiple PRs → uses first, logs warning."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        mock_has_remote.return_value = True
        mock_time.monotonic.side_effect = [0, 0, 100]
        mock_time.sleep = Mock()

        pr1 = {"number": 42, "url": "https://github.com/org/repo/pull/42"}
        pr2 = {"number": 43, "url": "https://github.com/org/repo/pull/43"}
        mock_pr_cls.return_value.find_pull_request_by_head.return_value = [pr1, pr2]

        mock_collect.return_value = _make_report()

        args = _make_base_args(wait_for_pr=True)
        with caplog.at_level(logging.DEBUG):
            result = execute_check_branch_status(args)

        assert result == 0
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("Multiple PRs" in r.message for r in warning_records)


# ---------------------------------------------------------------------------
# CI pending hint tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestCIPendingHint:
    """Tests for the CI pending hint after report display."""

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    def test_ci_pending_hint_when_timeout_zero(
        self,
        mock_collect: Mock,
        mock_resolve: Mock,
        mock_branch: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """CI pending + ci_timeout=0 → hint logged."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        mock_collect.return_value = _make_report(
            ci_status=CI_PENDING,
            recommendations=["Wait for CI to complete"],
        )

        args = _make_base_args(ci_timeout=0)
        with caplog.at_level(logging.DEBUG):
            result = execute_check_branch_status(args)

        assert result == 0
        assert any(
            "CI pending. Use --ci-timeout to wait for completion." in r.message
            for r in caplog.records
        )

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    def test_no_ci_hint_when_timeout_nonzero(
        self,
        mock_collect: Mock,
        mock_resolve: Mock,
        mock_branch: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """CI pending + ci_timeout>0 → no hint."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        mock_collect.return_value = _make_report(ci_status=CI_PENDING)

        # Need to mock CI waiting path too since ci_timeout > 0
        with (
            patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager"),
            patch(
                "mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion",
                return_value=(None, True),
            ),
            caplog.at_level(logging.DEBUG),
        ):
            args = _make_base_args(ci_timeout=180)
            execute_check_branch_status(args)

        assert not any(
            "CI pending. Use --ci-timeout to wait for completion." in r.message
            for r in caplog.records
        )

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    def test_no_ci_hint_when_ci_passed(
        self,
        mock_collect: Mock,
        mock_resolve: Mock,
        mock_branch: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """CI passed + ci_timeout=0 → no hint."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        mock_collect.return_value = _make_report(ci_status="PASSED")

        args = _make_base_args(ci_timeout=0)
        with caplog.at_level(logging.DEBUG):
            execute_check_branch_status(args)

        assert not any(
            "CI pending. Use --ci-timeout to wait for completion." in r.message
            for r in caplog.records
        )


# ---------------------------------------------------------------------------
# Existing behaviour preservation
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestNoPRWaitingSkipsPolling:
    """Verify that wait_for_pr=False preserves existing behaviour."""

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    def test_no_wait_for_pr_skips_polling(
        self,
        mock_collect: Mock,
        mock_resolve: Mock,
        mock_branch: Mock,
    ) -> None:
        """wait_for_pr=False → no PR manager created, normal flow, report.pr_found is None."""
        mock_resolve.return_value = Path("/test/project")
        mock_branch.return_value = "feature/xyz"
        report = _make_report()
        mock_collect.return_value = report

        args = _make_base_args(wait_for_pr=False)

        with patch(
            "mcp_coder.cli.commands.check_branch_status.PullRequestManager"
        ) as mock_pr_cls:
            result = execute_check_branch_status(args)

        assert result == 0
        mock_pr_cls.assert_not_called()
