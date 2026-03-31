"""Tests for gh-tool get-base-branch CLI command.

This module tests CLI-specific behavior (exit codes, output format, argument parsing).
Detection logic tests are in tests/workflow_utils/test_base_branch.py.
"""

import argparse
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.gh_tool import (
    execute_checkout_issue_branch,
    execute_get_base_branch,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_detect_base_branch() -> Generator[MagicMock, None, None]:
    """Mock detect_base_branch function."""
    with patch("mcp_coder.cli.commands.gh_tool.detect_base_branch") as mock:
        yield mock


@pytest.fixture
def mock_resolve_project_dir() -> Generator[MagicMock, None, None]:
    """Mock resolve_project_dir utility function."""
    with patch("mcp_coder.cli.commands.gh_tool.resolve_project_dir") as mock:
        yield mock


# ============================================================================
# Test Classes for Exit Codes
# ============================================================================


class TestGetBaseBranchExitCodes:
    """Tests for get-base-branch exit codes (0, 1, 2)."""

    def test_get_base_branch_exit_code_success(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 0 on successful detection."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "main"

    def test_get_base_branch_exit_code_detection_failure(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
    ) -> None:
        """Test exit code 1 when detection fails but no error occurred."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "unknown"

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 1

    def test_get_base_branch_exit_code_error_not_git_repo(
        self,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 2 when not a git repository."""
        mock_resolve_project_dir.side_effect = ValueError("Not a git repository")

        args = argparse.Namespace(project_dir="/not/a/repo")
        result = execute_get_base_branch(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_get_base_branch_exit_code_error_unexpected_exception(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 2 on unexpected exception."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.side_effect = Exception("Unexpected error")

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err


# ============================================================================
# Test Classes for Output Format
# ============================================================================


class TestGetBaseBranchOutputFormat:
    """Tests for get-base-branch output format (stdout only, no extra text)."""

    def test_get_base_branch_outputs_to_stdout(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that branch name is printed to stdout only."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "develop"

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        # stdout should contain ONLY the branch name (and newline)
        assert captured.out.strip() == "develop"
        # stderr should be empty on success
        assert captured.err == ""

    def test_get_base_branch_no_extra_text_in_output(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that output contains only branch name without labels or prefixes."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "release/v2.1"

        args = argparse.Namespace(project_dir=None)
        _ = execute_get_base_branch(args)

        captured = capsys.readouterr()
        # Should NOT contain labels like "Base branch:" or similar
        assert "Base" not in captured.out
        assert captured.out.strip() == "release/v2.1"


# ============================================================================
# Test Classes for CLI Integration
# ============================================================================


class TestGhToolCommandIntegration:
    """Test gh-tool command CLI integration."""

    def test_gh_tool_get_base_branch_command_exists(self) -> None:
        """Test that gh-tool get-base-branch is registered in CLI."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Check if gh-tool command exists in parser
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        assert subparsers_actions, "No subparsers found in CLI parser"

        subparser = subparsers_actions[0]
        assert "gh-tool" in subparser.choices, "gh-tool command should be registered"

    def test_gh_tool_help_shows_get_base_branch(self) -> None:
        """Test that gh-tool --help shows get-base-branch subcommand."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Get gh-tool subparser
        subparsers = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ][0]
        gh_tool_parser = subparsers.choices["gh-tool"]

        # Get subcommands of gh-tool
        gh_tool_subparsers = [
            action
            for action in gh_tool_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        assert gh_tool_subparsers, "gh-tool should have subparsers"

        gh_tool_subcommands = gh_tool_subparsers[0]
        assert (
            "get-base-branch" in gh_tool_subcommands.choices
        ), "get-base-branch should be a subcommand of gh-tool"

    def test_gh_tool_get_base_branch_help_shows_exit_codes(self) -> None:
        """Test that get-base-branch --help shows exit codes in epilog."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Navigate to get-base-branch parser
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
        get_base_branch_parser = gh_tool_subparsers.choices["get-base-branch"]

        # Check epilog contains exit code documentation
        epilog = get_base_branch_parser.epilog
        assert epilog is not None, "get-base-branch should have epilog"
        assert "0" in epilog, "Epilog should document exit code 0"
        assert "1" in epilog, "Epilog should document exit code 1"
        assert "2" in epilog, "Epilog should document exit code 2"

    def test_gh_tool_get_base_branch_command_calls_function(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
    ) -> None:
        """Test that gh-tool get-base-branch CLI command calls the execution function."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_detect_base_branch.return_value = "main"

        # Create args as CLI parser would
        args = argparse.Namespace(project_dir=None)

        result = execute_get_base_branch(args)

        assert result == 0
        mock_detect_base_branch.assert_called_once_with(project_dir)

    def test_gh_tool_get_base_branch_with_project_dir_option(
        self,
        mock_detect_base_branch: MagicMock,
        mock_resolve_project_dir: MagicMock,
    ) -> None:
        """Test --project-dir option is parsed correctly."""
        custom_dir = Path("/custom/path")
        mock_resolve_project_dir.return_value = custom_dir
        mock_detect_base_branch.return_value = "develop"

        # Create args as CLI parser would with custom project_dir
        args = argparse.Namespace(project_dir="/custom/path")

        result = execute_get_base_branch(args)

        assert result == 0
        # Verify resolve_project_dir was called with the custom path
        mock_resolve_project_dir.assert_called_once_with("/custom/path")
        mock_detect_base_branch.assert_called_once_with(custom_dir)


# ============================================================================
# Test Classes for gh-tool define-labels
# ============================================================================


class TestGhToolDefineLabelsIntegration:
    """Test gh-tool define-labels CLI integration."""

    def test_gh_tool_define_labels_command_exists(self) -> None:
        """define-labels is registered under gh-tool."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["gh-tool", "define-labels"])

        assert args.command == "gh-tool"
        assert args.gh_tool_subcommand == "define-labels"

    def test_gh_tool_define_labels_with_dry_run(self) -> None:
        """--dry-run flag is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["gh-tool", "define-labels", "--dry-run"])

        assert args.dry_run is True

    def test_gh_tool_define_labels_with_project_dir(self) -> None:
        """--project-dir is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["gh-tool", "define-labels", "--project-dir", "/my/project"]
        )

        assert args.project_dir == "/my/project"


# ============================================================================
# Test Classes for gh-tool issue-stats
# ============================================================================


class TestGhToolIssueStatsIntegration:
    """Test gh-tool issue-stats CLI integration."""

    def test_gh_tool_issue_stats_command_exists(self) -> None:
        """issue-stats is registered under gh-tool."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["gh-tool", "issue-stats"])

        assert args.command == "gh-tool"
        assert args.gh_tool_subcommand == "issue-stats"

    def test_gh_tool_issue_stats_default_values(self) -> None:
        """Default filter=all, details=False."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["gh-tool", "issue-stats"])

        assert args.filter == "all"
        assert args.details is False

    def test_gh_tool_issue_stats_with_filter(self) -> None:
        """--filter argument is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["gh-tool", "issue-stats", "--filter", "human"])

        assert args.filter == "human"

    def test_gh_tool_issue_stats_with_details(self) -> None:
        """--details flag is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["gh-tool", "issue-stats", "--details"])

        assert args.details is True


# ============================================================================
# Fixtures for checkout-issue-branch
# ============================================================================


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
        capsys: pytest.CaptureFixture[str],
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
        result = execute_checkout_issue_branch(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_checkout_git_checkout_fails(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_branch_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        mock_checkout_branch: MagicMock,
        capsys: pytest.CaptureFixture[str],
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
        result = execute_checkout_issue_branch(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_checkout_issue_not_found(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        capsys: pytest.CaptureFixture[str],
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
        result = execute_checkout_issue_branch(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_checkout_invalid_project_dir(
        self,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """resolve_project_dir raises ValueError -> exit 2."""
        mock_resolve_project_dir.side_effect = ValueError("Not a git repository")

        args = argparse.Namespace(issue_number=123, project_dir="/invalid/path")
        result = execute_checkout_issue_branch(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_checkout_unexpected_error(
        self,
        mock_resolve_project_dir: MagicMock,
        mock_issue_manager: MagicMock,
        mock_fetch_remote: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Unexpected exception -> exit 2."""
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_issue_manager.return_value.get_issue.side_effect = RuntimeError(
            "Unexpected"
        )

        args = argparse.Namespace(issue_number=123, project_dir=None)
        result = execute_checkout_issue_branch(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err


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
