"""Tests for gh-tool checkout-issue-branch CLI command."""

import argparse
import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.gh_tool import (
    _find_precreate_candidates,
    execute_checkout_issue_branch,
)

# ============================================================================
# Fixtures for checkout-issue-branch
# ============================================================================


@pytest.fixture
def mock_resolve_project_dir() -> Generator[MagicMock, None, None]:
    """Mock resolve_project_dir utility function."""
    with patch("mcp_coder.cli.commands.gh_tool.resolve_project_dir") as mock:
        mock.return_value = Path("/test/project")
        yield mock


@pytest.fixture
def mock_issue_manager() -> Generator[MagicMock, None, None]:
    """Mock IssueManager for checkout-issue-branch tests."""
    with patch("mcp_coder.cli.commands.gh_tool.IssueManager") as mock:
        mock.return_value.get_issue.return_value = {
            "number": 123,
            "title": "Test issue",
            "base_branch": "main",
        }
        yield mock


@pytest.fixture
def mock_branch_manager() -> Generator[MagicMock, None, None]:
    """Mock IssueBranchManager for checkout-issue-branch tests."""
    with patch("mcp_coder.cli.commands.gh_tool.IssueBranchManager") as mock:
        yield mock


@pytest.fixture
def mock_repo_identifier() -> Generator[MagicMock, None, None]:
    """Mock get_repository_identifier returning a valid repo id."""
    with patch("mcp_coder.cli.commands.gh_tool.get_repository_identifier") as mock:
        mock.return_value = MagicMock(
            owner="owner",
            repo_name="repo",
            https_url="https://github.com/owner/repo",
        )
        yield mock


def _remote_result(*branches: str, success: bool = True) -> dict[str, Any]:
    """Build a ``list_remote_branches`` result for the given branch names."""
    if not success:
        return {
            "success": False,
            "error": "git ls-remote failed (exit 1)",
            "returncode": 1,
            "stderr": "fatal: no remote",
            "branches": [],
        }
    return {
        "success": True,
        "error": None,
        "returncode": 0,
        "stderr": "",
        "branches": list(branches),
    }


@pytest.fixture
def mock_list_remote_branches() -> Generator[MagicMock, None, None]:
    """Mock list_remote_branches (success, no branches)."""
    with patch("mcp_coder.cli.commands.gh_tool.list_remote_branches") as mock:
        mock.return_value = _remote_result()
        yield mock


@pytest.fixture
def mock_fetch_remote() -> Generator[MagicMock, None, None]:
    """Mock fetch_remote for git fetch."""
    with patch("mcp_coder.cli.commands.gh_tool.fetch_remote") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_checkout_branch() -> Generator[MagicMock, None, None]:
    """Mock checkout_branch for git checkout."""
    with patch("mcp_coder.cli.commands.gh_tool.checkout_branch") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def checkout_mocks(
    mock_resolve_project_dir: MagicMock,
    mock_issue_manager: MagicMock,
    mock_branch_manager: MagicMock,
    mock_repo_identifier: MagicMock,
    mock_list_remote_branches: MagicMock,
    mock_fetch_remote: MagicMock,
    mock_checkout_branch: MagicMock,
) -> dict[str, MagicMock]:
    """All checkout-issue-branch mocks, keyed by short name."""
    return {
        "resolve": mock_resolve_project_dir,
        "issue": mock_issue_manager,
        "branch": mock_branch_manager,
        "repo_id": mock_repo_identifier,
        "remote": mock_list_remote_branches,
        "fetch": mock_fetch_remote,
        "checkout": mock_checkout_branch,
    }


# ============================================================================
# Test Classes for checkout-issue-branch Exit Codes
# ============================================================================


class TestCheckoutIssueBranchExitCodes:
    """Tests for checkout-issue-branch exit codes (0, 1, 2, 3)."""

    def test_checkout_existing_branch_success(
        self,
        checkout_mocks: dict[str, MagicMock],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Fallback finds a branch, checkout succeeds -> exit 0, branch name on stdout."""
        mgr = checkout_mocks["branch"].return_value
        mgr.get_branch_with_pr_fallback.return_value = "123-test-issue"

        args = argparse.Namespace(issue_number=123, project_dir=None)
        result = execute_checkout_issue_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "123-test-issue"
        mgr.get_branch_with_pr_fallback.assert_called_once_with(123, "owner", "repo")

    def test_checkout_constructs_real_branch_manager(
        self,
        github_remote_repo: Path,
        mock_fetch_remote: MagicMock,
        mock_checkout_branch: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The real IssueBranchManager constructor accepts the arguments passed."""
        with (
            patch(
                "mcp_coder.mcp_workspace_github.IssueManager.get_issue",
                return_value={"number": 123, "title": "T", "base_branch": "main"},
            ),
            patch(
                "mcp_coder.mcp_workspace_github.IssueBranchManager"
                ".get_branch_with_pr_fallback",
                return_value="123-test-issue",
            ) as fallback,
        ):
            args = argparse.Namespace(
                issue_number=123, project_dir=str(github_remote_repo)
            )
            result = execute_checkout_issue_branch(args)

        assert result == 0
        assert capsys.readouterr().out.strip() == "123-test-issue"
        fallback.assert_called_once_with(123, "owner", "repo")

    def test_checkout_creates_new_branch_success(
        self,
        checkout_mocks: dict[str, MagicMock],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No branch found, no candidates, creation succeeds -> exit 0."""
        checkout_mocks["issue"].return_value.get_issue.return_value = {
            "number": 456,
            "title": "New feature",
            "base_branch": "develop",
        }
        mgr = checkout_mocks["branch"].return_value
        mgr.get_branch_with_pr_fallback.return_value = None
        mgr.get_linked_branch_and_closing_prs_or_none.return_value = ([], [])
        mgr.create_remote_branch_for_issue.return_value = {
            "success": True,
            "branch_name": "456-new-feature",
            "error": None,
            "existing_branches": [],
        }

        args = argparse.Namespace(issue_number=456, project_dir=None)
        result = execute_checkout_issue_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "456-new-feature"
        checkout_mocks["remote"].assert_called_once_with(Path("/test/project"))

    def test_checkout_branch_creation_fails(
        self,
        checkout_mocks: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """No branch found, creation fails -> exit 1."""
        checkout_mocks["issue"].return_value.get_issue.return_value = {
            "number": 789,
            "title": "Some issue",
            "base_branch": "main",
        }
        mgr = checkout_mocks["branch"].return_value
        mgr.get_branch_with_pr_fallback.return_value = None
        mgr.get_linked_branch_and_closing_prs_or_none.return_value = ([], [])
        mgr.create_remote_branch_for_issue.return_value = {
            "success": False,
            "branch_name": "",
            "error": "API failure",
            "existing_branches": [],
        }

        args = argparse.Namespace(issue_number=789, project_dir=None)
        with caplog.at_level(logging.DEBUG):
            result = execute_checkout_issue_branch(args)

        assert result == 1
        assert "API failure" in caplog.text

    def test_checkout_git_checkout_fails(
        self,
        checkout_mocks: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Branch found but git checkout fails -> exit 2."""
        mgr = checkout_mocks["branch"].return_value
        mgr.get_branch_with_pr_fallback.return_value = "123-test-issue"
        checkout_mocks["checkout"].return_value = False

        args = argparse.Namespace(issue_number=123, project_dir=None)
        with caplog.at_level(logging.DEBUG):
            result = execute_checkout_issue_branch(args)

        assert result == 2
        assert "checkout failed" in caplog.text.lower()

    def test_checkout_issue_not_found(
        self,
        checkout_mocks: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """get_issue returns empty issue (number=0) -> exit 1."""
        checkout_mocks["issue"].return_value.get_issue.return_value = {
            "number": 0,
            "title": "",
            "base_branch": None,
        }

        args = argparse.Namespace(issue_number=999, project_dir=None)
        with caplog.at_level(logging.DEBUG):
            result = execute_checkout_issue_branch(args)

        assert result == 1
        assert "Could not find issue" in caplog.text

    def test_checkout_invalid_project_dir(
        self,
        mock_resolve_project_dir: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """resolve_project_dir raises ValueError -> exit 2."""
        mock_resolve_project_dir.side_effect = ValueError("Not a git repository")

        args = argparse.Namespace(issue_number=123, project_dir="/invalid/path")
        with caplog.at_level(logging.DEBUG):
            result = execute_checkout_issue_branch(args)

        assert result == 2
        assert "Not a git repository" in caplog.text

    def test_checkout_unexpected_error(
        self,
        checkout_mocks: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Unexpected exception -> exit 2."""
        checkout_mocks["issue"].return_value.get_issue.side_effect = RuntimeError(
            "Unexpected"
        )

        args = argparse.Namespace(issue_number=123, project_dir=None)
        with caplog.at_level(logging.DEBUG):
            result = execute_checkout_issue_branch(args)

        assert result == 2
        assert "Unexpected" in caplog.text

    @pytest.mark.parametrize(
        "case",
        ["no_repo_id", "lookup_none", "ls_remote_fails", "fallback_raises"],
    )
    def test_checkout_error_exit_2(
        self,
        checkout_mocks: dict[str, MagicMock],
        case: str,
    ) -> None:
        """Repo id, lookup, ls-remote or fallback failure -> exit 2, no create."""
        mgr = checkout_mocks["branch"].return_value
        mgr.get_branch_with_pr_fallback.return_value = None
        mgr.get_linked_branch_and_closing_prs_or_none.return_value = ([], [])
        if case == "no_repo_id":
            checkout_mocks["repo_id"].return_value = None
        elif case == "lookup_none":
            mgr.get_linked_branch_and_closing_prs_or_none.return_value = None
        elif case == "ls_remote_fails":
            checkout_mocks["remote"].return_value = _remote_result(success=False)
        else:
            mgr.get_branch_with_pr_fallback.side_effect = ValueError("API error")

        args = argparse.Namespace(issue_number=123, project_dir=None)
        result = execute_checkout_issue_branch(args)

        assert result == 2
        mgr.create_remote_branch_for_issue.assert_not_called()
        checkout_mocks["checkout"].assert_not_called()


# ============================================================================
# Test Classes for checkout-issue-branch Behavior
# ============================================================================


class TestCheckoutIssueBranchBehavior:
    """Tests for checkout-issue-branch behavioral correctness."""

    def test_checkout_pr_head_via_fallback(
        self,
        checkout_mocks: dict[str, MagicMock],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """PR open, linkedBranches empty: fallback returns PR head, nothing created."""
        mgr = checkout_mocks["branch"].return_value
        mgr.get_linked_branches.return_value = []
        mgr.get_branch_with_pr_fallback.return_value = "123-pr-head"

        args = argparse.Namespace(issue_number=123, project_dir=None)
        result = execute_checkout_issue_branch(args)

        assert result == 0
        assert capsys.readouterr().out.strip() == "123-pr-head"
        checkout_mocks["checkout"].assert_called_once_with(
            "123-pr-head", Path("/test/project")
        )
        mgr.create_remote_branch_for_issue.assert_not_called()
        mgr.get_linked_branch_and_closing_prs_or_none.assert_not_called()

    @pytest.mark.parametrize(
        ("lookup", "remote", "expected_branch", "expected_label"),
        [
            pytest.param(
                (["123-linked"], []),
                [],
                "123-linked",
                "linked branch 123-linked",
                id="one_linked",
            ),
            pytest.param(
                ([], [MagicMock(number=42, head_ref_name="123-b")]),
                [],
                "123-b",
                "closing PR #42 -> 123-b",
                id="one_closing_pr",
            ),
            pytest.param(
                ([], []),
                ["main", "123-remote"],
                "123-remote",
                "remote branch 123-remote",
                id="one_remote",
            ),
            pytest.param(
                ([], [MagicMock(number=42, head_ref_name="123-b")]),
                ["123-b"],
                "123-b",
                "closing PR #42 -> 123-b",
                id="closing_pr_and_remote_dedupe",
            ),
            pytest.param(
                ([], []),
                ["feature/123_x", "1234-x"],
                "feature/123_x",
                "remote branch feature/123_x",
                id="remote_prefix_match_ignores_1234",
            ),
        ],
    )
    def test_checkout_single_precreate_candidate(
        self,
        checkout_mocks: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
        lookup: tuple[list[str], list[Any]],
        remote: list[str],
        expected_branch: str,
        expected_label: str,
    ) -> None:
        """Exactly one pre-create candidate -> checked out, logged, nothing created."""
        mgr = checkout_mocks["branch"].return_value
        mgr.get_branch_with_pr_fallback.return_value = None
        mgr.get_linked_branch_and_closing_prs_or_none.return_value = lookup
        checkout_mocks["remote"].return_value = _remote_result(*remote)

        args = argparse.Namespace(issue_number=123, project_dir=None)
        with caplog.at_level(logging.INFO):
            result = execute_checkout_issue_branch(args)

        assert result == 0
        assert capsys.readouterr().out.strip() == expected_branch
        checkout_mocks["checkout"].assert_called_once_with(
            expected_branch, Path("/test/project")
        )
        mgr.create_remote_branch_for_issue.assert_not_called()
        assert expected_label in caplog.text

    @pytest.mark.parametrize(
        ("lookup", "remote", "expected_labels"),
        [
            pytest.param(
                (["123-first-branch", "123-second-branch"], []),
                [],
                [
                    "linked branch 123-first-branch",
                    "linked branch 123-second-branch",
                ],
                id="two_linked",
            ),
            pytest.param(
                (["123-linked"], [MagicMock(number=42, head_ref_name="123-b")]),
                [],
                ["linked branch 123-linked", "closing PR #42 -> 123-b"],
                id="linked_and_closing_pr",
            ),
            pytest.param(
                ([], []),
                ["123-a", "123-b"],
                ["remote branch 123-a", "remote branch 123-b"],
                id="two_remote",
            ),
        ],
    )
    def test_checkout_ambiguous_candidates_exit_3(
        self,
        checkout_mocks: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
        lookup: tuple[list[str], list[Any]],
        remote: list[str],
        expected_labels: list[str],
    ) -> None:
        """Two or more pre-create candidates -> exit 3, all logged, nothing created."""
        mgr = checkout_mocks["branch"].return_value
        mgr.get_branch_with_pr_fallback.return_value = None
        mgr.get_linked_branch_and_closing_prs_or_none.return_value = lookup
        checkout_mocks["remote"].return_value = _remote_result(*remote)

        args = argparse.Namespace(issue_number=123, project_dir=None)
        with caplog.at_level(logging.DEBUG):
            result = execute_checkout_issue_branch(args)

        assert result == 3
        for label in expected_labels:
            assert label in caplog.text
        mgr.create_remote_branch_for_issue.assert_not_called()
        checkout_mocks["checkout"].assert_not_called()

    def test_checkout_passes_base_branch_to_create(
        self,
        checkout_mocks: dict[str, MagicMock],
    ) -> None:
        """Verifies base_branch from issue data is passed to create_remote_branch_for_issue."""
        checkout_mocks["issue"].return_value.get_issue.return_value = {
            "number": 100,
            "title": "Feature",
            "base_branch": "develop",
        }
        mgr = checkout_mocks["branch"].return_value
        mgr.get_branch_with_pr_fallback.return_value = None
        mgr.get_linked_branch_and_closing_prs_or_none.return_value = ([], [])
        mgr.create_remote_branch_for_issue.return_value = {
            "success": True,
            "branch_name": "100-feature",
            "error": None,
            "existing_branches": [],
        }

        args = argparse.Namespace(issue_number=100, project_dir=None)
        execute_checkout_issue_branch(args)

        mgr.create_remote_branch_for_issue.assert_called_once_with(
            100, base_branch="develop"
        )

    def test_checkout_git_fetch_called_before_operations(
        self,
        checkout_mocks: dict[str, MagicMock],
    ) -> None:
        """Verifies git fetch is called."""
        mgr = checkout_mocks["branch"].return_value
        mgr.get_branch_with_pr_fallback.return_value = "123-test"

        args = argparse.Namespace(issue_number=123, project_dir=None)
        execute_checkout_issue_branch(args)

        checkout_mocks["fetch"].assert_called_once_with(Path("/test/project"))


class TestFindPrecreateCandidates:
    """Tests for _find_precreate_candidates remote branch handling."""

    def test_remote_branch_names_matched(
        self, mock_list_remote_branches: MagicMock
    ) -> None:
        """Branch names from list_remote_branches are matched against the issue."""
        mgr = MagicMock()
        mgr.get_linked_branch_and_closing_prs_or_none.return_value = ([], [])
        mock_list_remote_branches.return_value = _remote_result("123-feature", "other")

        result = _find_precreate_candidates(mgr, Path("/test/project"), 123)

        assert result == {"123-feature": "remote branch 123-feature"}
        mock_list_remote_branches.assert_called_once_with(Path("/test/project"))

    def test_remote_listing_failure_returns_none(
        self, mock_list_remote_branches: MagicMock
    ) -> None:
        """A failed remote listing is not an empty list -> None."""
        mgr = MagicMock()
        mgr.get_linked_branch_and_closing_prs_or_none.return_value = ([], [])
        mock_list_remote_branches.return_value = _remote_result(success=False)

        assert _find_precreate_candidates(mgr, Path("/test/project"), 123) is None


# ============================================================================
# Test Classes for checkout-issue-branch CLI Integration
# ============================================================================


class TestGhToolCheckoutIssueBranchIntegration:
    """Test gh-tool checkout-issue-branch CLI integration."""

    def test_checkout_issue_branch_command_exists(self) -> None:
        """checkout-issue-branch is registered under gh-tool."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["gh-tool", "checkout-issue-branch", "123"])

        assert args.command == "gh-tool"
        assert args.gh_tool_subcommand == "checkout-issue-branch"
        assert args.issue_number == 123

    def test_checkout_issue_branch_with_project_dir(self) -> None:
        """--project-dir is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "gh-tool",
                "checkout-issue-branch",
                "456",
                "--project-dir",
                "/my/project",
            ]
        )

        assert args.issue_number == 456
        assert args.project_dir == "/my/project"

    def test_checkout_issue_branch_help_shows_exit_codes(self) -> None:
        """Epilog documents exit codes."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Navigate to checkout-issue-branch parser
        subparsers = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ][0]
        gh_tool_parser = subparsers.choices["gh-tool"]

        gh_tool_subparsers = [
            action
            for action in gh_tool_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ][0]
        checkout_parser = gh_tool_subparsers.choices["checkout-issue-branch"]

        epilog = checkout_parser.epilog
        assert epilog is not None, "checkout-issue-branch should have epilog"
        assert "0" in epilog, "Epilog should document exit code 0"
        assert "1" in epilog, "Epilog should document exit code 1"
        assert "2" in epilog, "Epilog should document exit code 2"
        assert "3  Ambiguous" in epilog, "Epilog should document exit code 3"
