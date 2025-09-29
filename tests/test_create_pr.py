"""Tests for create_PR workflow cleanup functions."""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Import the functions we'll implement
from workflows.create_PR import (
    check_prerequisites,
    cleanup_repository,
    create_pull_request,
    delete_steps_directory,
    generate_pr_summary,
    main,
    parse_pr_summary,
    truncate_task_tracker,
)


class TestDeleteStepsDirectory:
    """Test delete_steps_directory function."""

    def test_delete_existing_directory(self) -> None:
        """Test successful deletion of existing pr_info/steps directory."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create pr_info/steps directory with some content
            steps_dir = project_dir / "pr_info" / "steps"
            steps_dir.mkdir(parents=True)

            # Add some test files
            (steps_dir / "step_1.md").write_text("Step 1 content")
            (steps_dir / "step_2.md").write_text("Step 2 content")

            # Create subdirectory with file
            sub_dir = steps_dir / "archived"
            sub_dir.mkdir()
            (sub_dir / "old_step.md").write_text("Old content")

            # Verify directory exists
            assert steps_dir.exists()
            assert (steps_dir / "step_1.md").exists()

            # Delete the directory
            result = delete_steps_directory(project_dir)

            # Verify deletion
            assert result is True
            assert not steps_dir.exists()

    def test_delete_missing_directory(self) -> None:
        """Test handling of missing pr_info/steps directory."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Ensure pr_info exists but not steps subdirectory
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            steps_dir = pr_info_dir / "steps"
            assert not steps_dir.exists()

            # Should return True (no-op for missing directory)
            result = delete_steps_directory(project_dir)
            assert result is True

    def test_delete_missing_pr_info(self) -> None:
        """Test handling when pr_info directory doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # No pr_info directory at all
            assert not (project_dir / "pr_info").exists()

            # Should return True (no-op)
            result = delete_steps_directory(project_dir)
            assert result is True

    @patch("workflows.create_PR.logger")
    def test_delete_with_permission_error(self, mock_logger: MagicMock) -> None:
        """Test handling of permission errors during deletion."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create directory
            steps_dir = project_dir / "pr_info" / "steps"
            steps_dir.mkdir(parents=True)

            # Mock shutil.rmtree only for the actual call, not for cleanup
            with patch("workflows.create_PR.shutil.rmtree") as mock_rmtree:
                # Simulate permission error
                mock_rmtree.side_effect = PermissionError("Access denied")

                # Should return False on error
                result = delete_steps_directory(project_dir)
                assert result is False

                # Should log error
                mock_logger.error.assert_called()

    @patch("workflows.create_PR.logger")
    def test_delete_with_logging(self, mock_logger: MagicMock) -> None:
        """Test that operations are properly logged."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create and delete directory
            steps_dir = project_dir / "pr_info" / "steps"
            steps_dir.mkdir(parents=True)

            result = delete_steps_directory(project_dir)
            assert result is True

            # Should log the operation
            mock_logger.info.assert_called()


class TestTruncateTaskTracker:
    """Test truncate_task_tracker function."""

    def test_truncate_at_tasks_section(self) -> None:
        """Test truncating TASK_TRACKER.md at '## Tasks' section."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create TASK_TRACKER.md with content
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            original_content = """# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in PR_Info/ folder

---

## Tasks

### Step 1: Setup
- [x] Task 1
- [ ] Task 2

### Step 2: Implementation
- [ ] Task 3
"""
            tracker_path.write_text(original_content, encoding="utf-8")

            # Truncate the file
            result = truncate_task_tracker(project_dir)
            assert result is True

            # Check truncated content
            truncated_content = tracker_path.read_text(encoding="utf-8")

            # Should keep everything before "## Tasks"
            assert "# Task Status Tracker" in truncated_content
            assert "## Instructions for LLM" in truncated_content
            assert "**Development Process:**" in truncated_content
            assert "---" in truncated_content

            # Should add "## Tasks" section but no task content
            assert truncated_content.strip().endswith("## Tasks")

            # Should not have any task content
            assert "### Step 1: Setup" not in truncated_content
            assert "- [x] Task 1" not in truncated_content
            assert "- [ ] Task 2" not in truncated_content

    def test_truncate_missing_tasks_section(self) -> None:
        """Test handling when '## Tasks' section is missing."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create TASK_TRACKER.md without Tasks section
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            original_content = """# Task Status Tracker

## Instructions for LLM

Some content here without Tasks section.
"""
            tracker_path.write_text(original_content, encoding="utf-8")

            # Should handle gracefully
            result = truncate_task_tracker(project_dir)
            assert result is True

            # Content should be unchanged but with ## Tasks added
            truncated_content = tracker_path.read_text(encoding="utf-8")
            assert "# Task Status Tracker" in truncated_content
            assert "## Instructions for LLM" in truncated_content
            assert "Some content here without Tasks section." in truncated_content
            assert truncated_content.strip().endswith("## Tasks")

    def test_truncate_missing_file(self) -> None:
        """Test handling of missing TASK_TRACKER.md file."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create pr_info but no TASK_TRACKER.md
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            assert not tracker_path.exists()

            # Should return False
            result = truncate_task_tracker(project_dir)
            assert result is False

    def test_truncate_missing_pr_info(self) -> None:
        """Test handling when pr_info directory doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # No pr_info directory
            assert not (project_dir / "pr_info").exists()

            # Should return False
            result = truncate_task_tracker(project_dir)
            assert result is False

    @patch("workflows.create_PR.logger")
    def test_truncate_with_logging(self, mock_logger: MagicMock) -> None:
        """Test that operations are properly logged."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create and truncate file
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            tracker_path.write_text(
                "# Header\n\n## Tasks\n\nSome tasks", encoding="utf-8"
            )

            result = truncate_task_tracker(project_dir)
            assert result is True

            # Should log the operation
            mock_logger.info.assert_called()

    def test_truncate_preserves_whitespace(self) -> None:
        """Test that truncation preserves original whitespace and formatting."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create file with specific whitespace
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            original_content = """# Task Status Tracker

## Instructions for LLM

Content with specific formatting.

---

## Tasks

Task content to remove.
"""
            tracker_path.write_text(original_content, encoding="utf-8")

            # Truncate
            result = truncate_task_tracker(project_dir)
            assert result is True

            # Check whitespace is preserved
            truncated = tracker_path.read_text(encoding="utf-8")
            expected = """# Task Status Tracker

## Instructions for LLM

Content with specific formatting.

---

## Tasks"""
            assert truncated == expected

    @patch("pathlib.Path.read_text", side_effect=PermissionError("Access denied"))
    @patch("workflows.create_PR.logger")
    def test_truncate_with_permission_error(
        self, mock_logger: MagicMock, mock_read_text: MagicMock
    ) -> None:
        """Test handling of permission errors during file operations."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pr_info_dir = project_dir / "pr_info"
            pr_info_dir.mkdir()

            # Create file
            tracker_path = pr_info_dir / "TASK_TRACKER.md"
            tracker_path.write_text("# Content", encoding="utf-8")

            # Should return False on error
            result = truncate_task_tracker(project_dir)
            assert result is False

            # Should log error
            mock_logger.error.assert_called()


class TestParsePrSummary:
    """Test parse_pr_summary function."""

    def test_parse_simple_response(self) -> None:
        """Test parsing simple LLM response with title and body."""
        response = """feat: Add new user authentication system

This PR implements a comprehensive authentication system with:
- JWT token management
- User registration and login
- Password reset functionality

Closes #123"""

        title, body = parse_pr_summary(response)

        assert title == "feat: Add new user authentication system"
        assert "This PR implements a comprehensive authentication system" in body
        assert (
            "feat: Add new user authentication system" in body
        )  # First line included in body
        assert "Closes #123" in body

    def test_parse_single_line_response(self) -> None:
        """Test parsing single line response (title only)."""
        response = "fix: Resolve database connection timeout issue"

        title, body = parse_pr_summary(response)

        assert title == "fix: Resolve database connection timeout issue"
        assert (
            body == "fix: Resolve database connection timeout issue"
        )  # Fallback includes first line

    def test_parse_empty_response(self) -> None:
        """Test parsing empty response."""
        response = ""

        title, body = parse_pr_summary(response)

        assert title == "Pull Request"
        assert body == "Pull Request"

    def test_parse_whitespace_only_response(self) -> None:
        """Test parsing response with only whitespace."""
        response = "   \n\n   \t   \n   "

        title, body = parse_pr_summary(response)

        assert title == "Pull Request"
        assert body == "Pull Request"

    def test_parse_multiline_with_empty_lines(self) -> None:
        """Test parsing response with empty lines."""
        response = """refactor: Improve code structure


This refactoring includes:

- Better separation of concerns
- Improved error handling


Tested with unit tests."""

        title, body = parse_pr_summary(response)

        assert title == "refactor: Improve code structure"
        assert "refactor: Improve code structure" in body
        assert "This refactoring includes" in body
        assert "Tested with unit tests." in body


class TestCheckPrerequisites:
    """Test check_prerequisites function."""

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    @patch("workflows.create_PR.get_current_branch_name")
    @patch("workflows.create_PR.get_parent_branch_name")
    def test_prerequisites_all_pass(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_incomplete_tasks: MagicMock,
        mock_clean: MagicMock,
    ) -> None:
        """Test prerequisites check when all conditions are met."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = []
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        result = check_prerequisites(Path("/test/project"))

        assert result is True
        mock_clean.assert_called_once()
        mock_incomplete_tasks.assert_called_once()
        mock_current_branch.assert_called_once()
        mock_parent_branch.assert_called_once()

    @patch("workflows.create_PR.is_working_directory_clean")
    def test_prerequisites_dirty_working_directory(self, mock_clean: MagicMock) -> None:
        """Test prerequisites check fails when working directory is dirty."""
        mock_clean.return_value = False

        result = check_prerequisites(Path("/test/project"))

        assert result is False
        mock_clean.assert_called_once()

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    def test_prerequisites_incomplete_tasks(
        self, mock_incomplete_tasks: MagicMock, mock_clean: MagicMock
    ) -> None:
        """Test prerequisites check fails when incomplete tasks exist."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = ["Incomplete task 1", "Incomplete task 2"]

        result = check_prerequisites(Path("/test/project"))

        assert result is False
        mock_clean.assert_called_once()
        mock_incomplete_tasks.assert_called_once()

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    @patch("workflows.create_PR.get_current_branch_name")
    @patch("workflows.create_PR.get_parent_branch_name")
    def test_prerequisites_same_branch(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_incomplete_tasks: MagicMock,
        mock_clean: MagicMock,
    ) -> None:
        """Test prerequisites check fails when current branch is parent branch."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = []
        mock_current_branch.return_value = "main"
        mock_parent_branch.return_value = "main"

        result = check_prerequisites(Path("/test/project"))

        assert result is False

    @patch("workflows.create_PR.is_working_directory_clean")
    @patch("workflows.create_PR.get_incomplete_tasks")
    @patch("workflows.create_PR.get_current_branch_name")
    def test_prerequisites_no_current_branch(
        self,
        mock_current_branch: MagicMock,
        mock_incomplete_tasks: MagicMock,
        mock_clean: MagicMock,
    ) -> None:
        """Test prerequisites check fails when current branch is unknown."""
        mock_clean.return_value = True
        mock_incomplete_tasks.return_value = []
        mock_current_branch.return_value = None

        result = check_prerequisites(Path("/test/project"))

        assert result is False


class TestGeneratePrSummary:
    """Test generate_pr_summary function."""

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR.get_prompt")
    @patch("workflows.create_PR.ask_llm")
    def test_generate_pr_summary_success(
        self,
        mock_ask_llm: MagicMock,
        mock_get_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test successful PR summary generation."""
        mock_get_diff.return_value = "diff content here"
        mock_get_prompt.return_value = "PR Summary prompt template"
        mock_ask_llm.return_value = "feat: Add authentication\n\nDetailed description"

        title, body = generate_pr_summary(Path("/test/project"))

        assert title == "feat: Add authentication"
        assert "Detailed description" in body
        mock_get_diff.assert_called_once_with(
            Path("/test/project"), exclude_paths=["pr_info/steps/"]
        )
        mock_get_prompt.assert_called_once()
        mock_ask_llm.assert_called_once()

    @patch("workflows.create_PR.get_branch_diff")
    def test_generate_pr_summary_no_diff(self, mock_get_diff: MagicMock) -> None:
        """Test PR summary generation when no diff available."""
        mock_get_diff.return_value = ""

        title, body = generate_pr_summary(Path("/test/project"))

        assert title == "Pull Request"
        assert body == "Pull Request"

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR.get_prompt")
    @patch("workflows.create_PR.ask_llm")
    def test_generate_pr_summary_llm_failure(
        self,
        mock_ask_llm: MagicMock,
        mock_get_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test PR summary generation when LLM call fails."""
        mock_get_diff.return_value = "diff content"
        mock_get_prompt.return_value = "prompt template"
        mock_ask_llm.return_value = None  # LLM failure

        # Should exit with code 1 on LLM failure
        with pytest.raises(SystemExit) as exc_info:
            generate_pr_summary(Path("/test/project"))
        
        assert exc_info.value.code == 1

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR.get_prompt")
    @patch("workflows.create_PR.ask_llm")
    def test_generate_pr_summary_llm_exception(
        self,
        mock_ask_llm: MagicMock,
        mock_get_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test PR summary generation when LLM call raises exception."""
        mock_get_diff.return_value = "diff content"
        mock_get_prompt.return_value = "prompt template"
        mock_ask_llm.side_effect = Exception("LLM API error")

        # Should exit with code 1 on LLM exception
        with pytest.raises(SystemExit) as exc_info:
            generate_pr_summary(Path("/test/project"))
        
        assert exc_info.value.code == 1


class TestCleanupRepository:
    """Test cleanup_repository function."""

    @patch("workflows.create_PR.delete_steps_directory")
    @patch("workflows.create_PR.truncate_task_tracker")
    def test_cleanup_repository_success(
        self, mock_truncate: MagicMock, mock_delete: MagicMock
    ) -> None:
        """Test successful repository cleanup."""
        mock_delete.return_value = True
        mock_truncate.return_value = True

        result = cleanup_repository(Path("/test/project"))

        assert result is True
        mock_delete.assert_called_once_with(Path("/test/project"))
        mock_truncate.assert_called_once_with(Path("/test/project"))

    @patch("workflows.create_PR.delete_steps_directory")
    @patch("workflows.create_PR.truncate_task_tracker")
    def test_cleanup_repository_delete_fails(
        self, mock_truncate: MagicMock, mock_delete: MagicMock
    ) -> None:
        """Test repository cleanup when delete_steps_directory fails."""
        mock_delete.return_value = False
        mock_truncate.return_value = True

        result = cleanup_repository(Path("/test/project"))

        assert result is False
        mock_delete.assert_called_once_with(Path("/test/project"))
        # Should still call truncate even if delete fails
        mock_truncate.assert_called_once_with(Path("/test/project"))

    @patch("workflows.create_PR.delete_steps_directory")
    @patch("workflows.create_PR.truncate_task_tracker")
    def test_cleanup_repository_truncate_fails(
        self, mock_truncate: MagicMock, mock_delete: MagicMock
    ) -> None:
        """Test repository cleanup when truncate_task_tracker fails."""
        mock_delete.return_value = True
        mock_truncate.return_value = False

        result = cleanup_repository(Path("/test/project"))

        assert result is False
        mock_delete.assert_called_once_with(Path("/test/project"))
        mock_truncate.assert_called_once_with(Path("/test/project"))

    @patch("workflows.create_PR.delete_steps_directory")
    @patch("workflows.create_PR.truncate_task_tracker")
    def test_cleanup_repository_both_fail(
        self, mock_truncate: MagicMock, mock_delete: MagicMock
    ) -> None:
        """Test repository cleanup when both operations fail."""
        mock_delete.return_value = False
        mock_truncate.return_value = False

        result = cleanup_repository(Path("/test/project"))

        assert result is False
        mock_delete.assert_called_once_with(Path("/test/project"))
        mock_truncate.assert_called_once_with(Path("/test/project"))


class TestCreatePullRequest:
    """Test create_pull_request function."""

    @patch("workflows.create_PR.PullRequestManager")
    @patch("workflows.create_PR.get_current_branch_name")
    @patch("workflows.create_PR.get_parent_branch_name")
    def test_create_pull_request_success(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_pr_manager: MagicMock,
    ) -> None:
        """Test successful pull request creation."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        mock_manager_instance = MagicMock()
        mock_manager_instance.create_pull_request.return_value = {
            "number": 123,
            "url": "https://github.com/owner/repo/pull/123",
        }
        mock_pr_manager.return_value = mock_manager_instance

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is True
        mock_pr_manager.assert_called_once_with(Path("/test/project"))
        mock_manager_instance.create_pull_request.assert_called_once_with(
            title="Test PR Title",
            head_branch="feature-branch",
            base_branch="main",
            body="Test PR Body",
        )

    @patch("workflows.create_PR.get_current_branch_name")
    def test_create_pull_request_no_current_branch(
        self, mock_current_branch: MagicMock
    ) -> None:
        """Test pull request creation when current branch is unknown."""
        mock_current_branch.return_value = None

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is False

    @patch("workflows.create_PR.PullRequestManager")
    @patch("workflows.create_PR.get_current_branch_name")
    @patch("workflows.create_PR.get_parent_branch_name")
    def test_create_pull_request_manager_failure(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_pr_manager: MagicMock,
    ) -> None:
        """Test pull request creation when PullRequestManager fails."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        mock_manager_instance = MagicMock()
        mock_manager_instance.create_pull_request.return_value = (
            {}
        )  # Empty dict indicates failure
        mock_pr_manager.return_value = mock_manager_instance

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is False

    @patch("workflows.create_PR.PullRequestManager")
    @patch("workflows.create_PR.get_current_branch_name")
    @patch("workflows.create_PR.get_parent_branch_name")
    def test_create_pull_request_exception(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_pr_manager: MagicMock,
    ) -> None:
        """Test pull request creation when exception occurs."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        mock_pr_manager.side_effect = Exception("GitHub API error")

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is False


class TestMainWorkflow:
    """Test main workflow function."""

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.create_pull_request")
    @patch("workflows.create_PR.cleanup_repository")
    @patch("workflows.create_PR.commit_all_changes")
    @patch("workflows.create_PR.git_push")
    @patch("workflows.create_PR.parse_arguments")
    def test_main_workflow_success(
        self,
        mock_parse_args: MagicMock,
        mock_git_push: MagicMock,
        mock_commit: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test successful complete workflow execution."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR Title", "Test PR Body")
        mock_create_pr.return_value = True
        mock_cleanup.return_value = True
        mock_commit.return_value = {"success": True, "commit_hash": "abc1234"}
        mock_git_push.return_value = {"success": True}

        # Should exit with code 0
        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_once_with(0)

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.parse_arguments")
    def test_main_workflow_prerequisites_fail(
        self,
        mock_parse_args: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow exits when prerequisites check fails."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = False

        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_once_with(1)

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.create_pull_request")
    @patch("workflows.create_PR.parse_arguments")
    def test_main_workflow_pr_creation_fails(
        self,
        mock_parse_args: MagicMock,
        mock_create_pr: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow exits when PR creation fails."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR Title", "Test PR Body")
        mock_create_pr.return_value = False  # PR creation fails

        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_once_with(1)

    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.create_pull_request")
    @patch("workflows.create_PR.cleanup_repository")
    @patch("workflows.create_PR.commit_all_changes")
    @patch("workflows.create_PR.git_push")
    @patch("workflows.create_PR.parse_arguments")
    @patch("workflows.create_PR.logger")
    def test_main_workflow_cleanup_fails(
        self,
        mock_logger: MagicMock,
        mock_parse_args: MagicMock,
        mock_git_push: MagicMock,
        mock_commit: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_setup_logging: MagicMock,
    ) -> None:
        """Test workflow continues when cleanup fails but logs warning."""
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR Title", "Test PR Body")
        mock_create_pr.return_value = True
        mock_cleanup.return_value = False  # Cleanup fails
        mock_commit.return_value = {"success": True, "commit_hash": "abc1234"}
        mock_git_push.return_value = {"success": True}

        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            # Should still exit successfully even if cleanup fails
            mock_exit.assert_called_once_with(0)
            # Should log warning about cleanup failure
            mock_logger.warning.assert_called()
