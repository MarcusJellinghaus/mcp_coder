"""Tests for gh-tool checkout-issue-branch CLI command."""

import argparse
import logging
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.gh_tool import execute_checkout_issue_branch

# ============================================================================
# Fixtures for checkout-issue-branch
# ============================================================================


@pytest.fixture
def mock_resolve_project_dir() -> Generator[MagicMock, None, None]:
    """Mock resolve_project_dir utility function."""
    with patch("mcp_coder.cli.commands.gh_tool.resolve_project_dir") as mock:
        yield mock


@pytest.fixture
def mock_issue_manager() -> Generator[MagicMock, None, None]:
    """Mock IssueManager for checkout-issue-branch tests."""
    with patch("mcp_coder.cli.commands.gh_tool.IssueManager") as mock:
        yield mock


@pytest.fixture
def mock_branch_manager() -> Generator[MagicMock, None, None]:
    """Mock IssueBranchManager for checkout-issue-branch tests."""
    with patch("mcp_coder.cli.commands.gh_tool.IssueBranchManager") as mock:
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


# ============================================================================
# Test Classes for checkout-issue-branch Exit Codes
# ============================================================================


class TestCheckoutIssueBranchExitCodes:
    """Tests for checkout-issue-branch exit codes (0, 1, 2)."""

    def test_checkout_existing_branch_success(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_branch_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        mock_checkout_branch: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Linked branch exists, checkout succeeds -> exit 0, branch name on stdout."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 123,
            "title": "Test issue",
            "base_branch": "main",
        }
        mock_branch_manager.return_value.get_linked_branches.return_value = [
            "123-test-issue"
        ]

        args = argparse.Namespace(issue_number=123, project_dir=None)
        result = execute_checkout_issue_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "123-test-issue"

    def test_checkout_creates_new_branch_success(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_branch_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        mock_checkout_branch: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No linked branches, creation succeeds, checkout succeeds -> exit 0."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 456,
            "title": "New feature",
            "base_branch": "develop",
        }
        mock_branch_manager.return_value.get_linked_branches.return_value = []
        mock_branch_manager.return_value.create_remote_branch_for_issue.return_value = {
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

    def test_checkout_branch_creation_fails(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_branch_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """No linked branches, creation fails -> exit 1."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 789,
            "title": "Some issue",
            "base_branch": "main",
        }
        mock_branch_manager.return_value.get_linked_branches.return_value = []
        mock_branch_manager.return_value.create_remote_branch_for_issue.return_value = {
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
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_branch_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        mock_checkout_branch: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Branch found but git checkout fails -> exit 2."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 123,
            "title": "Test issue",
            "base_branch": "main",
        }
        mock_branch_manager.return_value.get_linked_branches.return_value = [
            "123-test-issue"
        ]
        mock_checkout_branch.return_value = False

        args = argparse.Namespace(issue_number=123, project_dir=None)
        with caplog.at_level(logging.DEBUG):
            result = execute_checkout_issue_branch(args)

        assert result == 2
        assert "checkout failed" in caplog.text.lower()

    def test_checkout_issue_not_found(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """get_issue returns empty issue (number=0) -> exit 1."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.return_value = {
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
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Unexpected exception -> exit 2."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.side_effect = RuntimeError(
            "Unexpected"
        )

        args = argparse.Namespace(issue_number=123, project_dir=None)
        with caplog.at_level(logging.DEBUG):
            result = execute_checkout_issue_branch(args)

        assert result == 2
        assert "Unexpected" in caplog.text


# ============================================================================
# Test Classes for checkout-issue-branch Behavior
# ============================================================================


class TestCheckoutIssueBranchBehavior:
    """Tests for checkout-issue-branch behavioral correctness."""

    def test_checkout_uses_first_linked_branch(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_branch_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        mock_checkout_branch: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When multiple branches linked, uses first."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 123,
            "title": "Test",
            "base_branch": "main",
        }
        mock_branch_manager.return_value.get_linked_branches.return_value = [
            "123-first-branch",
            "123-second-branch",
        ]

        args = argparse.Namespace(issue_number=123, project_dir=None)
        result = execute_checkout_issue_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "123-first-branch"

    def test_checkout_passes_base_branch_to_create(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_branch_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        mock_checkout_branch: MagicMock,
    ) -> None:
        """Verifies base_branch from issue data is passed to create_remote_branch_for_issue."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 100,
            "title": "Feature",
            "base_branch": "develop",
        }
        mock_branch_manager.return_value.get_linked_branches.return_value = []
        mock_branch_manager.return_value.create_remote_branch_for_issue.return_value = {
            "success": True,
            "branch_name": "100-feature",
            "error": None,
            "existing_branches": [],
        }

        args = argparse.Namespace(issue_number=100, project_dir=None)
        execute_checkout_issue_branch(args)

        mock_branch_manager.return_value.create_remote_branch_for_issue.assert_called_once_with(
            100, base_branch="develop"
        )

    def test_checkout_git_fetch_called_before_operations(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_branch_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        mock_checkout_branch: MagicMock,
    ) -> None:
        """Verifies git fetch is called."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 123,
            "title": "Test",
            "base_branch": "main",
        }
        mock_branch_manager.return_value.get_linked_branches.return_value = ["123-test"]

        args = argparse.Namespace(issue_number=123, project_dir=None)
        execute_checkout_issue_branch(args)

        mock_fetch_remote.assert_called_once_with(project_dir)


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
