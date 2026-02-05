"""Tests for create_plan workflow main orchestration."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.create_plan import run_create_plan_workflow


class TestMain:
    """Test main workflow orchestration function."""

    @pytest.fixture
    def mock_issue_data(self) -> IssueData:
        """Create mock issue data for testing."""
        return IssueData(
            number=123,
            title="Test Issue",
            body="Test issue body",
            state="open",
            labels=["enhancement"],
            assignees=["testuser"],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

    def test_main_success_flow(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function with successful workflow execution."""
        # Create .git directory to satisfy git repo check
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=True,
                    ):
                        with patch(
                            "mcp_coder.workflows.create_plan.run_planning_prompts",
                            return_value=True,
                        ):
                            with patch(
                                "mcp_coder.workflows.create_plan.validate_output_files",
                                return_value=True,
                            ):
                                with patch(
                                    "mcp_coder.workflows.create_plan.commit_all_changes",
                                    return_value={
                                        "success": True,
                                        "commit_hash": "abc123",
                                    },
                                ):
                                    with patch(
                                        "mcp_coder.workflows.create_plan.git_push",
                                        return_value={"success": True},
                                    ):
                                        result = run_create_plan_workflow(
                                            123, tmp_path, "claude", "cli"
                                        )

        assert result == 0

    def test_main_execution_dir_passed_to_prompts(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test execution_dir parameter is passed to run_planning_prompts."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        # Create execution_dir
        exec_dir = tmp_path / "execution"
        exec_dir.mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=True,
                    ):
                        with patch(
                            "mcp_coder.workflows.create_plan.run_planning_prompts",
                            return_value=True,
                        ) as mock_prompts:
                            with patch(
                                "mcp_coder.workflows.create_plan.validate_output_files",
                                return_value=True,
                            ):
                                with patch(
                                    "mcp_coder.workflows.create_plan.commit_all_changes",
                                    return_value={
                                        "success": True,
                                        "commit_hash": "abc123",
                                    },
                                ):
                                    with patch(
                                        "mcp_coder.workflows.create_plan.git_push",
                                        return_value={"success": True},
                                    ):
                                        result = run_create_plan_workflow(
                                            123,
                                            tmp_path,
                                            "claude",
                                            "cli",
                                            None,
                                            exec_dir,
                                        )

        assert result == 0
        # Verify execution_dir was passed to run_planning_prompts
        mock_prompts.assert_called_once_with(
            tmp_path, mock_issue_data, "claude_code_cli", None, exec_dir
        )

    def test_main_prerequisites_fail(self, tmp_path: Path) -> None:
        """Test main function when prerequisites validation fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        empty_issue_data = IssueData(
            number=0,
            title="",
            body="",
            state="",
            labels=[],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="",
            locked=False,
        )

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(False, empty_issue_data),
        ):
            result = run_create_plan_workflow(123, tmp_path, "claude", "cli")

        assert result == 1

    def test_main_branch_management_fail(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when branch management fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch", return_value=None
            ):
                result = run_create_plan_workflow(123, tmp_path, "claude", "cli")

        assert result == 1

    def test_main_pr_info_exists(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when pr_info/ directory already exists."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=False,
                ):
                    result = run_create_plan_workflow(123, tmp_path, "claude", "cli")

        assert result == 1

    def test_main_create_pr_info_structure_fails(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when create_pr_info_structure fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=False,
                    ):
                        result = run_create_plan_workflow(
                            123, tmp_path, "claude", "cli"
                        )

        assert result == 1

    def test_main_planning_prompts_fail(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when planning prompts execution fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=True,
                    ):
                        with patch(
                            "mcp_coder.workflows.create_plan.run_planning_prompts",
                            return_value=False,
                        ):
                            result = run_create_plan_workflow(
                                123, tmp_path, "claude", "cli"
                            )

        assert result == 1

    def test_main_validation_fail(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when output files validation fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=True,
                    ):
                        with patch(
                            "mcp_coder.workflows.create_plan.run_planning_prompts",
                            return_value=True,
                        ):
                            with patch(
                                "mcp_coder.workflows.create_plan.validate_output_files",
                                return_value=False,
                            ):
                                result = run_create_plan_workflow(
                                    123, tmp_path, "claude", "cli"
                                )

        assert result == 1

    def test_main_commit_message_format(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function uses correct commit message format."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=True,
                    ):
                        with patch(
                            "mcp_coder.workflows.create_plan.run_planning_prompts",
                            return_value=True,
                        ):
                            with patch(
                                "mcp_coder.workflows.create_plan.validate_output_files",
                                return_value=True,
                            ):
                                with patch(
                                    "mcp_coder.workflows.create_plan.commit_all_changes"
                                ) as mock_commit:
                                    mock_commit.return_value = {
                                        "success": True,
                                        "commit_hash": "abc123",
                                    }
                                    with patch(
                                        "mcp_coder.workflows.create_plan.git_push",
                                        return_value={"success": True},
                                    ):
                                        result = run_create_plan_workflow(
                                            123, tmp_path, "claude", "cli"
                                        )

        # Verify commit message format
        mock_commit.assert_called_once()
        commit_message = mock_commit.call_args[0][0]
        assert commit_message == "Initial plan generated for issue #123"
        assert result == 0

    def test_main_commit_fails_continues(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function continues when commit fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=True,
                    ):
                        with patch(
                            "mcp_coder.workflows.create_plan.run_planning_prompts",
                            return_value=True,
                        ):
                            with patch(
                                "mcp_coder.workflows.create_plan.validate_output_files",
                                return_value=True,
                            ):
                                with patch(
                                    "mcp_coder.workflows.create_plan.commit_all_changes",
                                    return_value={
                                        "success": False,
                                        "error": "Commit failed",
                                    },
                                ):
                                    with patch(
                                        "mcp_coder.workflows.create_plan.git_push"
                                    ) as mock_push:
                                        mock_push.return_value = {"success": True}
                                        result = run_create_plan_workflow(
                                            123, tmp_path, "claude", "cli"
                                        )

        # Should still exit with success even if commit failed
        assert result == 0
        # Push should still be attempted
        mock_push.assert_called_once()

    def test_main_push_fails_continues(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function continues when push fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=True,
                    ):
                        with patch(
                            "mcp_coder.workflows.create_plan.run_planning_prompts",
                            return_value=True,
                        ):
                            with patch(
                                "mcp_coder.workflows.create_plan.validate_output_files",
                                return_value=True,
                            ):
                                with patch(
                                    "mcp_coder.workflows.create_plan.commit_all_changes",
                                    return_value={
                                        "success": True,
                                        "commit_hash": "abc123",
                                    },
                                ):
                                    with patch(
                                        "mcp_coder.workflows.create_plan.git_push",
                                        return_value={
                                            "success": False,
                                            "error": "Push failed",
                                        },
                                    ):
                                        result = run_create_plan_workflow(
                                            123, tmp_path, "claude", "cli"
                                        )

        # Should still exit with success even if push failed
        assert result == 0

    def test_main_with_custom_project_dir(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function with custom project directory."""
        # Create custom project directory with .git
        custom_dir = tmp_path / "custom_project"
        custom_dir.mkdir()
        (custom_dir / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ):
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=True,
                    ):
                        with patch(
                            "mcp_coder.workflows.create_plan.run_planning_prompts",
                            return_value=True,
                        ):
                            with patch(
                                "mcp_coder.workflows.create_plan.validate_output_files",
                                return_value=True,
                            ):
                                with patch(
                                    "mcp_coder.workflows.create_plan.commit_all_changes",
                                    return_value={
                                        "success": True,
                                        "commit_hash": "xyz789",
                                    },
                                ):
                                    with patch(
                                        "mcp_coder.workflows.create_plan.git_push",
                                        return_value={"success": True},
                                    ):
                                        result = run_create_plan_workflow(
                                            456, custom_dir, "claude_code", "api"
                                        )

        assert result == 0

    def test_main_logging_includes_issue_details(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function logs include issue number and title."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch(
            "mcp_coder.workflows.create_plan.check_prerequisites",
            return_value=(True, mock_issue_data),
        ) as mock_check:
            with patch(
                "mcp_coder.workflows.create_plan.manage_branch",
                return_value="feature-branch",
            ) as mock_manage:
                with patch(
                    "mcp_coder.workflows.create_plan.check_pr_info_not_exists",
                    return_value=True,
                ):
                    with patch(
                        "mcp_coder.workflows.create_plan.create_pr_info_structure",
                        return_value=True,
                    ):
                        with patch(
                            "mcp_coder.workflows.create_plan.run_planning_prompts",
                            return_value=True,
                        ) as mock_prompts:
                            with patch(
                                "mcp_coder.workflows.create_plan.validate_output_files",
                                return_value=True,
                            ):
                                with patch(
                                    "mcp_coder.workflows.create_plan.commit_all_changes",
                                    return_value={
                                        "success": True,
                                        "commit_hash": "abc123",
                                    },
                                ):
                                    with patch(
                                        "mcp_coder.workflows.create_plan.git_push",
                                        return_value={"success": True},
                                    ):
                                        result = run_create_plan_workflow(
                                            123, tmp_path, "claude", "cli"
                                        )

        # Verify functions were called with correct parameters
        mock_check.assert_called_once_with(tmp_path, 123)
        mock_manage.assert_called_once_with(
            tmp_path, 123, "Test Issue", base_branch=None
        )
        mock_prompts.assert_called_once_with(
            tmp_path, mock_issue_data, "claude_code_cli", None, None
        )
        assert result == 0
