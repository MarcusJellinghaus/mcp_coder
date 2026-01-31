"""Integration tests for create_PR workflow script.

These tests verify the complete workflow integration including:
- End-to-end workflow execution
- File system operations
- Git repository state management
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.git_operations import (
    commit_all_changes,
    get_current_branch_name,
    is_working_directory_clean,
)

# Import git fixtures from utils
from tests.utils.conftest import git_repo


class TestCreatePRWorkflowIntegration:
    """Integration tests for the complete PR creation workflow."""

    @pytest.mark.git_integration
    def test_workflow_prerequisite_validation(self, git_repo: tuple[Any, Path]) -> None:
        """Test that workflow properly validates prerequisites."""
        repo, project_dir = git_repo

        # Create minimal project structure
        self._setup_minimal_project(project_dir)

        # Test with dirty working directory
        test_file = project_dir / "dirty_file.txt"
        test_file.write_text("uncommitted content")

        # Import and test the prerequisite check
        from mcp_coder.workflows.create_pr.core import check_prerequisites

        # Should fail with dirty working directory
        assert not check_prerequisites(project_dir)

        # Clean up and test again
        test_file.unlink()

        # Should still fail due to missing task tracker
        assert not check_prerequisites(project_dir)

    @pytest.mark.git_integration
    def test_workflow_with_complete_project_structure(
        self, git_repo: tuple[Any, Path]
    ) -> None:
        """Test workflow with proper project structure and completed tasks."""
        repo, project_dir = git_repo

        # Setup complete project structure
        self._setup_complete_project(project_dir, repo)

        # Import workflow functions (get_current_branch_name and is_working_directory_clean already imported at module level)
        from mcp_coder.utils.git_operations import get_parent_branch_name
        from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks
        from mcp_coder.workflows.create_pr.core import check_prerequisites

        # Test each prerequisite individually
        is_clean = is_working_directory_clean(project_dir)
        current_branch = get_current_branch_name(project_dir)
        parent_branch = get_parent_branch_name(project_dir)

        # Test task tracker
        try:
            incomplete_tasks = get_incomplete_tasks(str(project_dir / "pr_info"))
        except Exception as e:
            pytest.fail(f"Task tracker check failed: {e}")

        # Individual assertions for better error messages
        assert is_clean, "Working directory not clean"
        assert current_branch is not None, "Could not get current branch name"
        assert (
            parent_branch is not None
        ), f"Could not get parent branch name: {parent_branch}"
        assert (
            current_branch != parent_branch
        ), f"Current branch '{current_branch}' equals parent branch '{parent_branch}'"
        assert len(incomplete_tasks) == 0, f"Found incomplete tasks: {incomplete_tasks}"

        # Should pass prerequisites now
        assert check_prerequisites(project_dir)

    @pytest.mark.git_integration
    def test_repository_cleanup_operations(self, git_repo: tuple[Any, Path]) -> None:
        """Test repository cleanup functions work correctly."""
        repo, project_dir = git_repo

        # Setup project with steps directory
        self._setup_project_with_steps(project_dir)

        # Import cleanup functions
        from mcp_coder.workflows.create_pr.core import (
            cleanup_repository,
            delete_pr_info_directory,
        )

        # Test delete_pr_info_directory operation
        assert delete_pr_info_directory(project_dir)
        assert not (project_dir / "pr_info").exists()

        # Recreate for full cleanup test
        self._setup_project_with_steps(project_dir)

        # Test full cleanup - should delete entire pr_info directory
        assert cleanup_repository(project_dir)
        assert not (project_dir / "pr_info").exists()

    @pytest.mark.git_integration
    def test_pr_summary_generation_with_diff(self, git_repo: tuple[Any, Path]) -> None:
        """Test PR summary generation with actual git diff."""
        repo, project_dir = git_repo

        # Setup project and make some changes
        self._setup_complete_project(project_dir, repo)

        # Create a feature branch
        repo.create_head("feature-branch")
        repo.heads["feature-branch"].checkout()

        # Make some changes
        feature_file = project_dir / "src" / "feature.py"
        feature_file.parent.mkdir(parents=True, exist_ok=True)
        feature_file.write_text("def new_feature():\n    return 'Hello World'")

        # Commit changes
        repo.index.add(["src/feature.py"])
        repo.index.commit("Add new feature")

        # Mock LLM response for PR summary
        with patch("mcp_coder.workflows.create_pr.core.ask_llm") as mock_llm:
            mock_llm.return_value = (
                "feat: Add new feature\n\nThis PR adds a new feature function."
            )

            from mcp_coder.workflows.create_pr.core import generate_pr_summary

            title, body = generate_pr_summary(
                project_dir, provider="claude", method="cli"
            )

            assert title == "feat: Add new feature"
            assert "This PR adds a new feature function." in body
            mock_llm.assert_called_once()

    @pytest.mark.git_integration
    def test_workflow_git_operations_integration(
        self, git_repo: tuple[Any, Path]
    ) -> None:
        """Test workflow integration with git operations."""
        repo, project_dir = git_repo

        # Setup complete project
        self._setup_complete_project(project_dir, repo)

        # Verify git operations work correctly
        assert is_working_directory_clean(project_dir)

        current_branch = get_current_branch_name(project_dir)
        # After _setup_complete_project, we should be on the feature branch
        assert current_branch == "feature-test-branch"

        # Test commit functionality
        test_file = project_dir / "test_commit.txt"
        test_file.write_text("test content")

        result = commit_all_changes("Test commit message", project_dir)
        assert result["success"]
        assert "commit_hash" in result

        # Verify commit was made
        commits = list(repo.iter_commits())
        assert len(commits) >= 2  # initial + test commit

    def _setup_minimal_project(self, project_dir: Path) -> None:
        """Setup minimal project structure for testing."""
        # Create basic source structure
        src_dir = project_dir / "src" / "mcp_coder"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create basic prompts file
        prompts_dir = project_dir / "src" / "mcp_coder" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "prompts.md").write_text(
            "# Prompts\n\n## PR Summary Generation\n\nGenerate PR summary from: [git_diff_content]"
        )

    def _setup_complete_project(self, project_dir: Path, repo: Any) -> None:
        """Setup complete project structure with all required components."""
        self._setup_minimal_project(project_dir)

        # Create pr_info structure
        pr_info_dir = project_dir / "pr_info"
        pr_info_dir.mkdir()

        # Create TASK_TRACKER.md with all tasks completed in proper format
        tracker_content = """# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

---

## Tasks

### Step 1: Complete
- [x] All tasks completed

### Step 2: Complete  
- [x] All tasks completed
"""
        (pr_info_dir / "TASK_TRACKER.md").write_text(tracker_content)

        # Commit initial structure
        repo.index.add(
            [
                str(f.relative_to(project_dir))
                for f in project_dir.rglob("*")
                if f.is_file()
            ]
        )
        repo.index.commit("Initial project structure")

        # Rename the default branch to 'main' if it's 'master'
        if repo.active_branch.name == "master":
            # Create main branch from master and switch to it
            main_branch = repo.create_head("main")
            main_branch.checkout()
            # Delete master branch
            repo.delete_head("master")

        # Create a feature branch so we're not on the parent branch
        feature_branch = repo.create_head("feature-test-branch")
        feature_branch.checkout()

        # Commit any additional changes if they exist (e.g., from branch operations)
        if repo.is_dirty() or repo.untracked_files:
            repo.index.add(repo.untracked_files if repo.untracked_files else [])
            if repo.is_dirty():
                repo.index.commit("Setup feature branch")

    def _setup_project_with_steps(self, project_dir: Path) -> None:
        """Setup project with pr_info/steps directory for cleanup testing."""
        # Create pr_info structure
        pr_info_dir = project_dir / "pr_info"
        pr_info_dir.mkdir(exist_ok=True)

        # Create steps directory with content
        steps_dir = pr_info_dir / "steps"
        steps_dir.mkdir(exist_ok=True)

        (steps_dir / "step_1.md").write_text("# Step 1\nDetails for step 1")
        (steps_dir / "step_2.md").write_text("# Step 2\nDetails for step 2")

        # Create subdirectory
        sub_dir = steps_dir / "archive"
        sub_dir.mkdir()
        (sub_dir / "old_step.md").write_text("Old step content")

        # Create TASK_TRACKER.md
        tracker_content = """# Task Status Tracker

## Instructions for LLM

Instructions here.

---

## Tasks

### Step 1: Setup
- [x] Task 1
- [ ] Task 2

### Step 2: Implementation  
- [ ] Task 3
"""
        (pr_info_dir / "TASK_TRACKER.md").write_text(tracker_content)


class TestWorkflowErrorHandling:
    """Test error handling in the PR creation workflow."""

    @pytest.mark.git_integration
    def test_workflow_handles_missing_files_gracefully(self, tmp_path: Path) -> None:
        """Test that workflow handles missing files gracefully."""
        project_dir = tmp_path / "empty_project"
        project_dir.mkdir()

        from mcp_coder.workflows.create_pr.core import (
            check_prerequisites,
            cleanup_repository,
        )

        # Should handle missing files without crashing
        assert not check_prerequisites(project_dir)  # Should return False, not crash

        # Cleanup should handle missing directories gracefully (returns True for no-op)
        assert cleanup_repository(
            project_dir
        )  # Should return True when nothing to clean

    @pytest.mark.git_integration
    def test_workflow_handles_permission_errors(
        self, git_repo: tuple[Any, Path]
    ) -> None:
        """Test workflow behavior with permission errors."""
        repo, project_dir = git_repo

        # Setup basic structure
        pr_info_dir = project_dir / "pr_info"
        pr_info_dir.mkdir()

        (pr_info_dir / "TASK_TRACKER.md").write_text("# Task Tracker")

        from mcp_coder.workflows.create_pr.core import delete_pr_info_directory

        # Mock permission error
        with patch("mcp_coder.workflows.create_pr.core.shutil.rmtree") as mock_rmtree:
            mock_rmtree.side_effect = PermissionError("Access denied")

            # Should return False and log error, not crash
            result = delete_pr_info_directory(project_dir)
            assert result is False

    def test_parse_pr_summary_edge_cases(self) -> None:
        """Test PR summary parsing with various edge cases."""
        from mcp_coder.workflows.create_pr.core import parse_pr_summary

        # Test empty response
        title, body = parse_pr_summary("")
        assert title == "Pull Request"
        assert body == "Pull Request"

        # Test whitespace only
        title, body = parse_pr_summary("   \n\n   ")
        assert title == "Pull Request"
        assert body == "Pull Request"

        # Test single line
        title, body = parse_pr_summary("feat: Add feature")
        assert title == "feat: Add feature"
        assert body == "feat: Add feature"

        # Test multiline
        response = "feat: Add feature\n\nDetailed description here"
        title, body = parse_pr_summary(response)
        assert title == "feat: Add feature"
        assert body == response


class TestWorkflowMainFunction:
    """Test the main workflow orchestration function."""

    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    def test_main_workflow_prerequisite_failure(
        self,
        mock_check_prereqs: MagicMock,
    ) -> None:
        """Test main workflow exits early when prerequisites fail."""
        # Setup mocks
        mock_check_prereqs.return_value = False  # Fail prerequisites to exit early

        from mcp_coder.workflows.create_pr.core import run_create_pr_workflow

        # Should return 1 due to failed prerequisites
        result = run_create_pr_workflow(
            Path("/test/project"), provider="claude", method="cli"
        )
        assert result == 1

        # Verify prerequisite check was called
        mock_check_prereqs.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    def test_main_workflow_pr_creation_failure(
        self,
        mock_create_pr: MagicMock,
        mock_git_push: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
    ) -> None:
        """Test main workflow handles PR creation failure."""
        # Setup mocks for successful prerequisites but failed PR creation
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR", "Test body")
        mock_git_push.return_value = {"success": True}  # Push succeeds
        mock_create_pr.return_value = False  # PR creation fails

        from mcp_coder.workflows.create_pr.core import run_create_pr_workflow

        # Should return 1 due to failed PR creation
        result = run_create_pr_workflow(
            Path("/test/project"), provider="claude", method="cli"
        )
        assert result == 1

        # Verify the workflow got to PR creation step
        mock_generate_summary.assert_called_once_with(
            Path("/test/project"), "claude", "cli", None, None
        )
        mock_create_pr.assert_called_once_with(
            Path("/test/project"), "Test PR", "Test body"
        )
