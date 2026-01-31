"""Tests for gh-tool get-base-branch command functionality.

This follows test-first development approach. Tests are written before implementation
of the gh-tool command module. Tests that require the gh_tool module are conditionally
skipped if the module doesn't exist yet.
"""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Test-first approach: Try to import the module, skip dependent tests if not available
try:
    from mcp_coder.cli.commands.gh_tool import execute_get_base_branch

    GH_TOOL_MODULE_AVAILABLE = True
except ImportError:
    GH_TOOL_MODULE_AVAILABLE = False

    # Create a mock for type checking in tests
    def execute_get_base_branch(*args, **kwargs):  # type: ignore
        pass


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_pr_manager():
    """Mock PullRequestManager with configurable PR data."""
    with patch("mcp_coder.cli.commands.gh_tool.PullRequestManager") as mock:
        yield mock


@pytest.fixture
def mock_issue_manager():
    """Mock IssueManager for issue lookup."""
    with patch("mcp_coder.cli.commands.gh_tool.IssueManager") as mock:
        yield mock


@pytest.fixture
def mock_git_readers():
    """Mock git reader functions."""
    with (
        patch("mcp_coder.cli.commands.gh_tool.get_current_branch_name") as mock_branch,
        patch(
            "mcp_coder.cli.commands.gh_tool.extract_issue_number_from_branch"
        ) as mock_extract,
        patch("mcp_coder.cli.commands.gh_tool.get_default_branch_name") as mock_default,
    ):
        yield mock_branch, mock_extract, mock_default


@pytest.fixture
def mock_resolve_project_dir():
    """Mock resolve_project_dir utility function."""
    with patch("mcp_coder.cli.commands.gh_tool.resolve_project_dir") as mock:
        yield mock


# ============================================================================
# Test Classes for Detection Priority Scenarios (PR → Issue → Default)
# ============================================================================


@pytest.mark.skipif(
    not GH_TOOL_MODULE_AVAILABLE,
    reason="gh_tool module not yet implemented",
)
class TestGetBaseBranchDetectionPriority:
    """Tests for base branch detection priority: PR → Issue → Default."""

    def test_get_base_branch_from_open_pr(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test detection from open PR base branch (highest priority)."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: current branch has an open PR targeting 'develop'
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature-name"
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature-name", "base_branch": "develop"}
        ]

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "develop"
        # PR manager should be called
        mock_pr_manager.return_value.list_pull_requests.assert_called_once()
        # Issue manager should NOT be called when PR exists
        mock_issue_manager.return_value.get_issue.assert_not_called()

    def test_get_base_branch_from_issue_body(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test detection from linked issue's ### Base Branch section."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: no open PR, but issue has base_branch field
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature-name"
        mock_extract.return_value = 370
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "title": "Test Issue",
            "body": "### Base Branch\n\nrelease/v2\n\n### Description",
            "base_branch": "release/v2",
        }

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "release/v2"
        # Issue manager should be called since no PR exists
        mock_issue_manager.return_value.get_issue.assert_called_once_with(370)

    def test_get_base_branch_falls_back_to_default(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test fallback to default branch (main/master) when no PR or issue base."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: no open PR, issue has no base_branch
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature-name"
        mock_extract.return_value = 370
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "title": "Test Issue",
            "body": "No base branch specified",
            "base_branch": None,
        }

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "main"
        # Default branch should be fetched
        mock_default.assert_called_once_with(project_dir)

    def test_get_base_branch_pr_takes_priority_over_issue(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that PR base branch has higher priority than issue base branch."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: both PR and issue have base branches - PR should win
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature-name"
        mock_extract.return_value = 370
        # PR targets 'develop'
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature-name", "base_branch": "develop"}
        ]
        # Issue specifies 'release/v2' - should be ignored
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": "release/v2",
        }

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "develop"  # PR branch, not issue branch
        # Issue manager should NOT be called when PR exists
        mock_issue_manager.return_value.get_issue.assert_not_called()

    def test_get_base_branch_issue_takes_priority_over_default(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that issue base branch has higher priority than default branch."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        # Setup: no PR, issue has base branch, default is 'main'
        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature-name"
        mock_extract.return_value = 370
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        # Issue specifies 'release/v2'
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": "release/v2",
        }

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "release/v2"  # Issue branch, not default
        # Default branch should NOT be fetched when issue has base_branch
        mock_default.assert_not_called()


# ============================================================================
# Test Classes for Exit Codes
# ============================================================================


@pytest.mark.skipif(
    not GH_TOOL_MODULE_AVAILABLE,
    reason="gh_tool module not yet implemented",
)
class TestGetBaseBranchExitCodes:
    """Tests for get-base-branch exit codes (0, 1, 2)."""

    def test_get_base_branch_exit_code_success(
        self,
        mock_pr_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 0 on successful detection."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature"
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature", "base_branch": "main"}
        ]

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0

    def test_get_base_branch_exit_code_detection_failure(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 1 when detection fails but no error occurred."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "feature-no-issue"
        mock_extract.return_value = None  # No issue number in branch
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        mock_default.return_value = None  # No default branch found

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 1

    def test_get_base_branch_exit_code_error_not_git_repo(
        self,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 2 when not a git repository."""
        # resolve_project_dir exits with code 1 on failure
        mock_resolve_project_dir.side_effect = SystemExit(1)

        args = argparse.Namespace(project_dir="/not/a/repo")

        with pytest.raises(SystemExit) as exc_info:
            execute_get_base_branch(args)

        assert exc_info.value.code == 1

    def test_get_base_branch_exit_code_error_api_failure(
        self,
        mock_pr_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test exit code 2 on API error (GitHub API failure)."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature"
        # Simulate API error
        mock_pr_manager.return_value.list_pull_requests.side_effect = Exception(
            "GitHub API error"
        )

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err or "error" in captured.err.lower()


# ============================================================================
# Test Classes for Output Format
# ============================================================================


@pytest.mark.skipif(
    not GH_TOOL_MODULE_AVAILABLE,
    reason="gh_tool module not yet implemented",
)
class TestGetBaseBranchOutputFormat:
    """Tests for get-base-branch output format (stdout only, no extra text)."""

    def test_get_base_branch_outputs_to_stdout(
        self,
        mock_pr_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that branch name is printed to stdout only."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature"
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature", "base_branch": "develop"}
        ]

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
        mock_pr_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that output contains only branch name without labels or prefixes."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature"
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature", "base_branch": "release/v2.1"}
        ]

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        captured = capsys.readouterr()
        # Should NOT contain labels like "Base branch:" or similar
        assert "Base" not in captured.out
        assert "branch" not in captured.out.lower() or captured.out.strip() == "main"
        assert captured.out.strip() == "release/v2.1"


# ============================================================================
# Test Classes for CLI Integration
# ============================================================================


@pytest.mark.skipif(
    not GH_TOOL_MODULE_AVAILABLE,
    reason="gh_tool module not yet implemented",
)
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

    @patch("mcp_coder.cli.commands.gh_tool.execute_get_base_branch")
    @patch("sys.argv", ["mcp-coder", "gh-tool", "get-base-branch"])
    def test_gh_tool_get_base_branch_command_calls_function(
        self, mock_execute: Mock
    ) -> None:
        """Test that gh-tool get-base-branch CLI command calls the execution function."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that the function was called with proper arguments
        call_args = mock_execute.call_args[0][0]
        assert isinstance(call_args, argparse.Namespace)
        assert hasattr(call_args, "project_dir")

    @patch("mcp_coder.cli.commands.gh_tool.execute_get_base_branch")
    @patch(
        "sys.argv",
        ["mcp-coder", "gh-tool", "get-base-branch", "--project-dir", "/custom/path"],
    )
    def test_gh_tool_get_base_branch_with_project_dir_option(
        self, mock_execute: Mock
    ) -> None:
        """Test --project-dir option is parsed correctly."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0

        result = main()

        assert result == 0
        call_args = mock_execute.call_args[0][0]
        assert call_args.project_dir == "/custom/path"


# ============================================================================
# Test Classes for Edge Cases
# ============================================================================


@pytest.mark.skipif(
    not GH_TOOL_MODULE_AVAILABLE,
    reason="gh_tool module not yet implemented",
)
class TestGetBaseBranchEdgeCases:
    """Tests for edge cases in get-base-branch command."""

    def test_get_base_branch_no_current_branch(
        self,
        mock_pr_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test when not on any branch (detached HEAD state)."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = None  # Detached HEAD
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        # Should fall back to default branch
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "main"

    def test_get_base_branch_branch_without_issue_number(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test when branch name doesn't contain issue number."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "feature-without-issue"
        mock_extract.return_value = None  # No issue number extracted
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        # Should fall back to default branch (skipping issue lookup)
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "main"
        # Issue manager should NOT be called when no issue number
        mock_issue_manager.return_value.get_issue.assert_not_called()

    def test_get_base_branch_with_project_dir_option(
        self,
        mock_pr_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test --project-dir option works correctly."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        custom_dir = Path("/custom/project/path")
        mock_resolve_project_dir.return_value = custom_dir
        mock_branch.return_value = "370-feature"
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "370-feature", "base_branch": "main"}
        ]

        args = argparse.Namespace(project_dir="/custom/project/path")
        result = execute_get_base_branch(args)

        assert result == 0
        mock_resolve_project_dir.assert_called_once_with("/custom/project/path")

    def test_get_base_branch_pr_for_different_branch(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that PR for different branch is ignored."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "370-feature"
        mock_extract.return_value = 370
        mock_default.return_value = "main"
        # PR exists but for different branch
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "other-branch", "base_branch": "develop"}
        ]
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 370,
            "base_branch": None,
        }

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        assert result == 0
        captured = capsys.readouterr()
        # Should use default since PR is for different branch
        assert captured.out.strip() == "main"

    def test_get_base_branch_issue_not_found(
        self,
        mock_pr_manager: MagicMock,
        mock_issue_manager: MagicMock,
        mock_git_readers: tuple,
        mock_resolve_project_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test when issue cannot be found."""
        mock_branch, mock_extract, mock_default = mock_git_readers

        project_dir = Path("/test/project")
        mock_resolve_project_dir.return_value = project_dir
        mock_branch.return_value = "999-nonexistent"
        mock_extract.return_value = 999
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = []
        # Issue returns empty dict (not found)
        mock_issue_manager.return_value.get_issue.return_value = {
            "number": 0,
            "base_branch": None,
        }

        args = argparse.Namespace(project_dir=None)
        result = execute_get_base_branch(args)

        # Should fall back to default
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "main"
