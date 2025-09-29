"""Integration tests for create_PR workflow script.

These tests verify the complete workflow integration including:
- Windows batch wrapper functionality
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
from tests.utils.conftest import git_repo, git_repo_with_files


class TestCreatePRBatchWrapper:
    """Test Windows batch wrapper functionality."""

    def test_batch_file_exists(self) -> None:
        """Test that the batch wrapper file exists and is executable."""
        batch_file = Path("workflows/create_PR.bat")
        assert batch_file.exists(), "create_PR.bat wrapper should exist"
        assert batch_file.is_file(), "create_PR.bat should be a file"

        # Check file has content
        content = batch_file.read_text(encoding="utf-8")
        assert len(content) > 0, "Batch file should not be empty"
        assert "@echo off" in content, "Should be a proper Windows batch file"

    def test_batch_file_structure(self) -> None:
        """Test that batch file has proper structure and commands."""
        batch_file = Path("workflows/create_PR.bat")
        content = batch_file.read_text(encoding="utf-8")

        # Check for essential components
        assert "create_PR.py" in content, "Should reference the Python script"
        assert "python" in content.lower(), "Should call Python"
        assert "exit /b" in content, "Should properly handle exit codes"
        assert (
            "workflows\\create_PR.py" in content
        ), "Should reference correct script path"
        assert "PYTHONPATH" in content, "Should set PYTHONPATH for src directory"

    def test_batch_file_help_documentation(self) -> None:
        """Test that batch file contains proper usage documentation."""
        batch_file = Path("workflows/create_PR.bat")
        content = batch_file.read_text(encoding="utf-8")

        # Check for usage documentation
        assert "Usage:" in content, "Should have usage documentation"
        assert "--project-dir" in content, "Should document project-dir parameter"
        assert "--log-level" in content, "Should document log-level parameter"
        assert "Examples:" in content, "Should have usage examples"

    @pytest.mark.git_integration
    def test_batch_wrapper_environment_checks(self, tmp_path: Path) -> None:
        """Test batch wrapper environment validation."""
        # Create a temporary directory structure
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        # Copy the batch file to test directory
        original_batch = Path("workflows/create_PR.bat")
        test_batch = test_project / "workflows"
        test_batch.mkdir()

        # Create a modified batch file that just does environment checks
        test_batch_file = test_batch / "create_PR.bat"
        original_content = original_batch.read_text(encoding="utf-8")

        # Replace the Python execution with just environment checks
        test_content = original_content.replace(
            "python workflows\\create_PR.py %*", "echo Environment checks passed"
        )
        test_batch_file.write_text(test_content, encoding="utf-8")

        # Test environment check behavior (Python availability, etc.)
        # Note: This is a basic structure test, actual execution would require Windows


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
        from workflows.create_PR import check_prerequisites

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

        # Import workflow functions
        from mcp_coder.utils.git_operations import (
            get_current_branch_name,
            get_parent_branch_name,
            is_working_directory_clean,
        )
        from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks
        from workflows.create_PR import check_prerequisites

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
        assert is_clean, f"Working directory not clean"
        assert current_branch is not None, f"Could not get current branch name"
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
        from workflows.create_PR import (
            cleanup_repository,
            delete_steps_directory,
            truncate_task_tracker,
        )

        # Test individual cleanup operations
        assert delete_steps_directory(project_dir)
        assert not (project_dir / "pr_info" / "steps").exists()

        # Recreate for full cleanup test
        self._setup_project_with_steps(project_dir)

        # Test full cleanup
        assert cleanup_repository(project_dir)
        assert not (project_dir / "pr_info" / "steps").exists()

        # Check task tracker truncation
        tracker_content = (project_dir / "pr_info" / "TASK_TRACKER.md").read_text()
        assert tracker_content.strip().endswith("## Tasks")

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
        with patch("workflows.create_PR.ask_llm") as mock_llm:
            mock_llm.return_value = (
                "feat: Add new feature\n\nThis PR adds a new feature function."
            )

            from workflows.create_PR import generate_pr_summary

            title, body = generate_pr_summary(project_dir)

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

        from workflows.create_PR import check_prerequisites, cleanup_repository

        # Should handle missing files without crashing
        assert not check_prerequisites(project_dir)  # Should return False, not crash

        # Cleanup should handle missing directories
        assert not cleanup_repository(
            project_dir
        )  # Should return False for missing files

    @pytest.mark.git_integration
    def test_workflow_handles_permission_errors(
        self, git_repo: tuple[Any, Path]
    ) -> None:
        """Test workflow behavior with permission errors."""
        repo, project_dir = git_repo

        # Setup basic structure
        pr_info_dir = project_dir / "pr_info"
        pr_info_dir.mkdir()

        steps_dir = pr_info_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "test.md").write_text("test content")

        from workflows.create_PR import delete_steps_directory

        # Mock permission error
        with patch("workflows.create_PR.shutil.rmtree") as mock_rmtree:
            mock_rmtree.side_effect = PermissionError("Access denied")

            # Should return False and log error, not crash
            result = delete_steps_directory(project_dir)
            assert result is False

    def test_parse_pr_summary_edge_cases(self) -> None:
        """Test PR summary parsing with various edge cases."""
        from workflows.create_PR import parse_pr_summary

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

    @patch("workflows.create_PR.parse_arguments")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.check_prerequisites")
    def test_main_workflow_argument_handling(
        self,
        mock_check_prereqs: MagicMock,
        mock_setup_logging: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_parse_args: MagicMock,
    ) -> None:
        """Test main workflow argument parsing and setup."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = False  # Fail prerequisites to exit early

        from workflows.create_PR import main

        # Should exit with code 1 due to failed prerequisites
        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_with(1)

        # Verify setup was called
        mock_parse_args.assert_called_once()
        mock_resolve_dir.assert_called_once()
        mock_setup_logging.assert_called_once_with("INFO")
        mock_check_prereqs.assert_called_once()

    @patch("workflows.create_PR.parse_arguments")
    @patch("workflows.create_PR.resolve_project_dir")
    @patch("workflows.create_PR.setup_logging")
    @patch("workflows.create_PR.check_prerequisites")
    @patch("workflows.create_PR.generate_pr_summary")
    @patch("workflows.create_PR.git_push")
    @patch("workflows.create_PR.create_pull_request")
    def test_main_workflow_pr_creation_failure(
        self,
        mock_create_pr: MagicMock,
        mock_git_push: MagicMock,
        mock_generate_summary: MagicMock,
        mock_check_prereqs: MagicMock,
        mock_setup_logging: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_parse_args: MagicMock,
    ) -> None:
        """Test main workflow handles PR creation failure."""
        # Setup mocks for successful prerequisites but failed PR creation
        mock_args = MagicMock()
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args

        mock_resolve_dir.return_value = Path("/test/project")
        mock_check_prereqs.return_value = True
        mock_generate_summary.return_value = ("Test PR", "Test body")
        mock_git_push.return_value = {"success": True}  # Push succeeds
        mock_create_pr.return_value = False  # PR creation fails

        from workflows.create_PR import main

        # Should exit with code 1 due to failed PR creation
        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_with(1)

        # Verify the workflow got to PR creation step
        mock_generate_summary.assert_called_once()
        mock_create_pr.assert_called_once_with(
            Path("/test/project"), "Test PR", "Test body"
        )
