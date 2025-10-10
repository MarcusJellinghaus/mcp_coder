"""Tests for create_plan workflow main orchestration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.github_operations.issue_manager import IssueData
from workflows.create_plan import main


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

    @pytest.fixture
    def mock_args(self) -> MagicMock:
        """Create mock command line arguments."""
        args = MagicMock()
        args.issue_number = 123
        args.project_dir = None
        args.log_level = "INFO"
        args.llm_method = "claude_code_cli"
        return args

    def test_main_success_flow(
        self, mock_args: MagicMock, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function with successful workflow execution."""
        # Create .git directory to satisfy git repo check
        (tmp_path / ".git").mkdir()

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ):
                        with patch(
                            "workflows.create_plan.manage_branch",
                            return_value="feature-branch",
                        ):
                            with patch(
                                "workflows.create_plan.verify_steps_directory",
                                return_value=True,
                            ):
                                with patch(
                                    "workflows.create_plan.run_planning_prompts",
                                    return_value=True,
                                ):
                                    with patch(
                                        "workflows.create_plan.validate_output_files",
                                        return_value=True,
                                    ):
                                        with patch(
                                            "workflows.create_plan.commit_all_changes",
                                            return_value={
                                                "success": True,
                                                "commit_hash": "abc123",
                                            },
                                        ):
                                            with patch(
                                                "workflows.create_plan.git_push",
                                                return_value={"success": True},
                                            ):
                                                with pytest.raises(
                                                    SystemExit
                                                ) as exc_info:
                                                    main()

        assert exc_info.value.code == 0

    def test_main_prerequisites_fail(
        self, mock_args: MagicMock, tmp_path: Path
    ) -> None:
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

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(False, empty_issue_data),
                    ):
                        with pytest.raises(SystemExit) as exc_info:
                            main()

        assert exc_info.value.code == 1

    def test_main_branch_management_fail(
        self, mock_args: MagicMock, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when branch management fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ):
                        with patch(
                            "workflows.create_plan.manage_branch", return_value=None
                        ):
                            with pytest.raises(SystemExit) as exc_info:
                                main()

        assert exc_info.value.code == 1

    def test_main_steps_directory_not_empty(
        self, mock_args: MagicMock, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when steps directory is not empty."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ):
                        with patch(
                            "workflows.create_plan.manage_branch",
                            return_value="feature-branch",
                        ):
                            with patch(
                                "workflows.create_plan.verify_steps_directory",
                                return_value=False,
                            ):
                                with pytest.raises(SystemExit) as exc_info:
                                    main()

        assert exc_info.value.code == 1

    def test_main_planning_prompts_fail(
        self, mock_args: MagicMock, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when planning prompts execution fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ):
                        with patch(
                            "workflows.create_plan.manage_branch",
                            return_value="feature-branch",
                        ):
                            with patch(
                                "workflows.create_plan.verify_steps_directory",
                                return_value=True,
                            ):
                                with patch(
                                    "workflows.create_plan.run_planning_prompts",
                                    return_value=False,
                                ):
                                    with pytest.raises(SystemExit) as exc_info:
                                        main()

        assert exc_info.value.code == 1

    def test_main_validation_fail(
        self, mock_args: MagicMock, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function when output files validation fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ):
                        with patch(
                            "workflows.create_plan.manage_branch",
                            return_value="feature-branch",
                        ):
                            with patch(
                                "workflows.create_plan.verify_steps_directory",
                                return_value=True,
                            ):
                                with patch(
                                    "workflows.create_plan.run_planning_prompts",
                                    return_value=True,
                                ):
                                    with patch(
                                        "workflows.create_plan.validate_output_files",
                                        return_value=False,
                                    ):
                                        with pytest.raises(SystemExit) as exc_info:
                                            main()

        assert exc_info.value.code == 1

    def test_main_commit_message_format(
        self, mock_args: MagicMock, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function uses correct commit message format."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ):
                        with patch(
                            "workflows.create_plan.manage_branch",
                            return_value="feature-branch",
                        ):
                            with patch(
                                "workflows.create_plan.verify_steps_directory",
                                return_value=True,
                            ):
                                with patch(
                                    "workflows.create_plan.run_planning_prompts",
                                    return_value=True,
                                ):
                                    with patch(
                                        "workflows.create_plan.validate_output_files",
                                        return_value=True,
                                    ):
                                        with patch(
                                            "workflows.create_plan.commit_all_changes"
                                        ) as mock_commit:
                                            mock_commit.return_value = {
                                                "success": True,
                                                "commit_hash": "abc123",
                                            }
                                            with patch(
                                                "workflows.create_plan.git_push",
                                                return_value={"success": True},
                                            ):
                                                with pytest.raises(SystemExit):
                                                    main()

        # Verify commit message format
        mock_commit.assert_called_once()
        commit_message = mock_commit.call_args[0][0]
        assert commit_message == "Initial plan generated for issue #123"

    def test_main_commit_fails_continues(
        self, mock_args: MagicMock, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function continues when commit fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ):
                        with patch(
                            "workflows.create_plan.manage_branch",
                            return_value="feature-branch",
                        ):
                            with patch(
                                "workflows.create_plan.verify_steps_directory",
                                return_value=True,
                            ):
                                with patch(
                                    "workflows.create_plan.run_planning_prompts",
                                    return_value=True,
                                ):
                                    with patch(
                                        "workflows.create_plan.validate_output_files",
                                        return_value=True,
                                    ):
                                        with patch(
                                            "workflows.create_plan.commit_all_changes",
                                            return_value={
                                                "success": False,
                                                "error": "Commit failed",
                                            },
                                        ):
                                            with patch(
                                                "workflows.create_plan.git_push"
                                            ) as mock_push:
                                                mock_push.return_value = {
                                                    "success": True
                                                }
                                                with pytest.raises(
                                                    SystemExit
                                                ) as exc_info:
                                                    main()

        # Should still exit with success even if commit failed
        assert exc_info.value.code == 0
        # Push should still be attempted
        mock_push.assert_called_once()

    def test_main_push_fails_continues(
        self, mock_args: MagicMock, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function continues when push fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ):
                        with patch(
                            "workflows.create_plan.manage_branch",
                            return_value="feature-branch",
                        ):
                            with patch(
                                "workflows.create_plan.verify_steps_directory",
                                return_value=True,
                            ):
                                with patch(
                                    "workflows.create_plan.run_planning_prompts",
                                    return_value=True,
                                ):
                                    with patch(
                                        "workflows.create_plan.validate_output_files",
                                        return_value=True,
                                    ):
                                        with patch(
                                            "workflows.create_plan.commit_all_changes",
                                            return_value={
                                                "success": True,
                                                "commit_hash": "abc123",
                                            },
                                        ):
                                            with patch(
                                                "workflows.create_plan.git_push",
                                                return_value={
                                                    "success": False,
                                                    "error": "Push failed",
                                                },
                                            ):
                                                with pytest.raises(
                                                    SystemExit
                                                ) as exc_info:
                                                    main()

        # Should still exit with success even if push failed
        assert exc_info.value.code == 0

    def test_main_with_custom_project_dir(
        self, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function with custom project directory."""
        # Create custom project directory with .git
        custom_dir = tmp_path / "custom_project"
        custom_dir.mkdir()
        (custom_dir / ".git").mkdir()

        args = MagicMock()
        args.issue_number = 456
        args.project_dir = str(custom_dir)
        args.log_level = "DEBUG"
        args.llm_method = "claude_code_api"

        with patch("workflows.create_plan.parse_arguments", return_value=args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=custom_dir
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ):
                        with patch(
                            "workflows.create_plan.manage_branch",
                            return_value="feature-branch",
                        ):
                            with patch(
                                "workflows.create_plan.verify_steps_directory",
                                return_value=True,
                            ):
                                with patch(
                                    "workflows.create_plan.run_planning_prompts",
                                    return_value=True,
                                ):
                                    with patch(
                                        "workflows.create_plan.validate_output_files",
                                        return_value=True,
                                    ):
                                        with patch(
                                            "workflows.create_plan.commit_all_changes",
                                            return_value={
                                                "success": True,
                                                "commit_hash": "xyz789",
                                            },
                                        ):
                                            with patch(
                                                "workflows.create_plan.git_push",
                                                return_value={"success": True},
                                            ):
                                                with pytest.raises(SystemExit):
                                                    main()

    def test_main_logging_includes_issue_details(
        self, mock_args: MagicMock, mock_issue_data: IssueData, tmp_path: Path
    ) -> None:
        """Test main function logs include issue number and title."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
            with patch(
                "workflows.create_plan.resolve_project_dir", return_value=tmp_path
            ):
                with patch("workflows.create_plan.setup_logging"):
                    with patch(
                        "workflows.create_plan.check_prerequisites",
                        return_value=(True, mock_issue_data),
                    ) as mock_check:
                        with patch(
                            "workflows.create_plan.manage_branch",
                            return_value="feature-branch",
                        ) as mock_manage:
                            with patch(
                                "workflows.create_plan.verify_steps_directory",
                                return_value=True,
                            ):
                                with patch(
                                    "workflows.create_plan.run_planning_prompts",
                                    return_value=True,
                                ) as mock_prompts:
                                    with patch(
                                        "workflows.create_plan.validate_output_files",
                                        return_value=True,
                                    ):
                                        with patch(
                                            "workflows.create_plan.commit_all_changes",
                                            return_value={
                                                "success": True,
                                                "commit_hash": "abc123",
                                            },
                                        ):
                                            with patch(
                                                "workflows.create_plan.git_push",
                                                return_value={"success": True},
                                            ):
                                                with pytest.raises(SystemExit):
                                                    main()

        # Verify functions were called with correct parameters
        mock_check.assert_called_once_with(tmp_path, 123)
        mock_manage.assert_called_once_with(tmp_path, 123, "Test Issue")
        mock_prompts.assert_called_once_with(
            tmp_path, mock_issue_data, "claude_code_cli"
        )
