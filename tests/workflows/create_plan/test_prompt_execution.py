"""Tests for create_plan workflow prompt execution functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.workflows.create_plan import (
    _load_prompt_or_exit,
    format_initial_prompt,
    run_planning_prompts,
    validate_output_files,
)


class TestLoadPromptOrExit:
    """Test _load_prompt_or_exit function."""

    def test_load_prompt_or_exit_success(self) -> None:
        """Test _load_prompt_or_exit with successful prompt loading."""
        mock_prompt = "This is a test prompt template"

        with patch(
            "mcp_coder.workflows.create_plan.get_prompt", return_value=mock_prompt
        ):
            result = _load_prompt_or_exit("Test Header")

        assert result == mock_prompt

    def test_load_prompt_or_exit_file_not_found(self) -> None:
        """Test _load_prompt_or_exit when prompt file is not found."""
        with patch(
            "mcp_coder.workflows.create_plan.get_prompt",
            side_effect=FileNotFoundError("Prompt file not found"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                _load_prompt_or_exit("Test Header")

            assert exc_info.value.code == 1

    def test_load_prompt_or_exit_value_error(self) -> None:
        """Test _load_prompt_or_exit when prompt header is invalid."""
        with patch(
            "mcp_coder.workflows.create_plan.get_prompt",
            side_effect=ValueError("Invalid prompt header"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                _load_prompt_or_exit("Invalid Header")

            assert exc_info.value.code == 1

    def test_load_prompt_or_exit_unexpected_error(self) -> None:
        """Test _load_prompt_or_exit with unexpected error."""
        with patch(
            "mcp_coder.workflows.create_plan.get_prompt",
            side_effect=RuntimeError("Unexpected error"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                _load_prompt_or_exit("Test Header")

            assert exc_info.value.code == 1


class TestFormatInitialPrompt:
    """Test format_initial_prompt function."""

    def test_format_initial_prompt(self) -> None:
        """Test format_initial_prompt with basic issue data."""
        prompt_template = "Please analyze the following issue:"
        issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="This is a test issue body",
            state="open",
            labels=["bug"],
            assignees=["testuser"],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        result = format_initial_prompt(prompt_template, issue_data)

        assert "Please analyze the following issue:" in result
        assert "---" in result
        assert "## Issue to Implement:" in result
        assert "**Title:** Test Issue" in result
        assert "**Number:** #123" in result
        assert "**Description:**" in result
        assert "This is a test issue body" in result

    def test_format_initial_prompt_multiline_body(self) -> None:
        """Test format_initial_prompt with multiline issue body."""
        prompt_template = "Analyze this:"
        issue_data = IssueData(
            number=456,
            title="Multiline Issue",
            body="Line 1\nLine 2\nLine 3",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/456",
            locked=False,
        )

        result = format_initial_prompt(prompt_template, issue_data)

        assert "Line 1\nLine 2\nLine 3" in result

    def test_format_initial_prompt_empty_body(self) -> None:
        """Test format_initial_prompt with empty issue body."""
        prompt_template = "Test prompt"
        issue_data = IssueData(
            number=789,
            title="Empty Body Issue",
            body="",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/789",
            locked=False,
        )

        result = format_initial_prompt(prompt_template, issue_data)

        assert "**Title:** Empty Body Issue" in result
        assert "**Number:** #789" in result
        assert "**Description:**" in result


class TestRunPlanningPrompts:
    """Test run_planning_prompts function."""

    def test_run_planning_prompts_success(self, tmp_path: Path) -> None:
        """Test run_planning_prompts with successful execution of all prompts."""
        issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        # Mock prompts
        mock_prompts = {
            "Initial Analysis": "Prompt 1",
            "Simplification Review": "Prompt 2",
            "Implementation Plan Creation": "Prompt 3",
        }

        # Mock responses
        mock_response_1 = {"text": "Response 1", "session_id": "test-session-123"}
        mock_response_2 = {"text": "Response 2", "session_id": "test-session-123"}
        mock_response_3 = {"text": "Response 3", "session_id": "test-session-123"}

        with patch("mcp_coder.workflows.create_plan.get_prompt") as mock_get_prompt:
            mock_get_prompt.side_effect = lambda _, header: mock_prompts[header]

            with patch(
                "mcp_coder.workflows.create_plan.parse_llm_method",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.prompt_llm"
                ) as mock_prompt_llm:
                    mock_prompt_llm.side_effect = [
                        mock_response_1,
                        mock_response_2,
                        mock_response_3,
                    ]

                    result = run_planning_prompts(
                        tmp_path, issue_data, "claude_code_cli"
                    )

        assert result is True
        assert mock_prompt_llm.call_count == 3

        # Verify first call includes formatted prompt
        first_call_args = mock_prompt_llm.call_args_list[0]
        assert "Test Issue" in first_call_args[0][0]
        assert first_call_args[1]["session_id"] is None

        # Verify second and third calls use session_id
        second_call_args = mock_prompt_llm.call_args_list[1]
        assert second_call_args[1]["session_id"] == "test-session-123"

        third_call_args = mock_prompt_llm.call_args_list[2]
        assert third_call_args[1]["session_id"] == "test-session-123"

    def test_run_planning_prompts_first_fails(self, tmp_path: Path) -> None:
        """Test run_planning_prompts when first prompt fails."""
        issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        with patch(
            "mcp_coder.workflows.create_plan.get_prompt", return_value="Test prompt"
        ):
            with patch(
                "mcp_coder.workflows.create_plan.parse_llm_method",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.prompt_llm",
                    side_effect=Exception("LLM error"),
                ):
                    result = run_planning_prompts(
                        tmp_path, issue_data, "claude_code_cli"
                    )

        assert result is False

    def test_run_planning_prompts_session_continuation(self, tmp_path: Path) -> None:
        """Test run_planning_prompts properly continues session across prompts."""
        issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        mock_session_id = "unique-session-456"
        mock_response_1 = {"text": "Response 1", "session_id": mock_session_id}
        mock_response_2 = {"text": "Response 2", "session_id": mock_session_id}
        mock_response_3 = {"text": "Response 3", "session_id": mock_session_id}

        with patch(
            "mcp_coder.workflows.create_plan.get_prompt", return_value="Test prompt"
        ):
            with patch(
                "mcp_coder.workflows.create_plan.parse_llm_method",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.prompt_llm"
                ) as mock_prompt_llm:
                    mock_prompt_llm.side_effect = [
                        mock_response_1,
                        mock_response_2,
                        mock_response_3,
                    ]

                    result = run_planning_prompts(
                        tmp_path, issue_data, "claude_code_cli"
                    )

        assert result is True

        # Verify session_id is passed correctly
        call_args = mock_prompt_llm.call_args_list
        assert call_args[0][1]["session_id"] is None
        assert call_args[1][1]["session_id"] == mock_session_id
        assert call_args[2][1]["session_id"] == mock_session_id

    def test_run_planning_prompts_empty_response(self, tmp_path: Path) -> None:
        """Test run_planning_prompts when response is empty."""
        issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        mock_response = {"text": "", "session_id": "test-session"}

        with patch(
            "mcp_coder.workflows.create_plan.get_prompt", return_value="Test prompt"
        ):
            with patch(
                "mcp_coder.workflows.create_plan.parse_llm_method",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.prompt_llm",
                    return_value=mock_response,
                ):
                    result = run_planning_prompts(
                        tmp_path, issue_data, "claude_code_cli"
                    )

        assert result is False

    def test_run_planning_prompts_no_session_id(self, tmp_path: Path) -> None:
        """Test run_planning_prompts when first response has no session_id."""
        issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        mock_response = {"text": "Response text"}  # Missing session_id

        with patch(
            "mcp_coder.workflows.create_plan.get_prompt", return_value="Test prompt"
        ):
            with patch(
                "mcp_coder.workflows.create_plan.parse_llm_method",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.prompt_llm",
                    return_value=mock_response,
                ):
                    result = run_planning_prompts(
                        tmp_path, issue_data, "claude_code_cli"
                    )

        assert result is False

    def test_run_planning_prompts_invalid_llm_method(self, tmp_path: Path) -> None:
        """Test run_planning_prompts with invalid LLM method."""
        issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        with patch(
            "mcp_coder.workflows.create_plan.get_prompt", return_value="Test prompt"
        ):
            with patch(
                "mcp_coder.workflows.create_plan.parse_llm_method",
                side_effect=ValueError("Invalid method"),
            ):
                result = run_planning_prompts(tmp_path, issue_data, "invalid_method")

        assert result is False

    def test_run_planning_prompts_second_prompt_fails(self, tmp_path: Path) -> None:
        """Test run_planning_prompts when second prompt fails."""
        issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        mock_response_1 = {"text": "Response 1", "session_id": "test-session"}

        with patch(
            "mcp_coder.workflows.create_plan.get_prompt", return_value="Test prompt"
        ):
            with patch(
                "mcp_coder.workflows.create_plan.parse_llm_method",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.prompt_llm"
                ) as mock_prompt_llm:
                    mock_prompt_llm.side_effect = [
                        mock_response_1,
                        Exception("Second prompt failed"),
                    ]

                    result = run_planning_prompts(
                        tmp_path, issue_data, "claude_code_cli"
                    )

        assert result is False

    def test_run_planning_prompts_third_prompt_fails(self, tmp_path: Path) -> None:
        """Test run_planning_prompts when third prompt fails."""
        issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            labels=[],
            assignees=[],
            user="author",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/test/repo/issues/123",
            locked=False,
        )

        mock_response_1 = {"text": "Response 1", "session_id": "test-session"}
        mock_response_2 = {"text": "Response 2", "session_id": "test-session"}

        with patch(
            "mcp_coder.workflows.create_plan.get_prompt", return_value="Test prompt"
        ):
            with patch(
                "mcp_coder.workflows.create_plan.parse_llm_method",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.prompt_llm"
                ) as mock_prompt_llm:
                    mock_prompt_llm.side_effect = [
                        mock_response_1,
                        mock_response_2,
                        Exception("Third prompt failed"),
                    ]

                    result = run_planning_prompts(
                        tmp_path, issue_data, "claude_code_cli"
                    )

        assert result is False


class TestValidateOutputFiles:
    """Test validate_output_files function."""

    def test_validate_output_files_both_exist(self, tmp_path: Path) -> None:
        """Test validate_output_files when both required files exist."""
        # Create required directories and files
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        summary_file = steps_dir / "summary.md"
        summary_file.write_text("Summary content")

        step_1_file = steps_dir / "step_1.md"
        step_1_file.write_text("Step 1 content")

        result = validate_output_files(tmp_path)

        assert result is True

    def test_validate_output_files_missing_summary(self, tmp_path: Path) -> None:
        """Test validate_output_files when summary.md is missing."""
        # Create directory and only step_1.md
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        step_1_file = steps_dir / "step_1.md"
        step_1_file.write_text("Step 1 content")

        result = validate_output_files(tmp_path)

        assert result is False

    def test_validate_output_files_missing_step_1(self, tmp_path: Path) -> None:
        """Test validate_output_files when step_1.md is missing."""
        # Create directory and only summary.md
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        summary_file = steps_dir / "summary.md"
        summary_file.write_text("Summary content")

        result = validate_output_files(tmp_path)

        assert result is False

    def test_validate_output_files_both_missing(self, tmp_path: Path) -> None:
        """Test validate_output_files when both files are missing."""
        # Create directory but no files
        steps_dir = tmp_path / "pr_info" / "steps"
        steps_dir.mkdir(parents=True)

        result = validate_output_files(tmp_path)

        assert result is False

    def test_validate_output_files_directory_missing(self, tmp_path: Path) -> None:
        """Test validate_output_files when pr_info/steps directory doesn't exist."""
        result = validate_output_files(tmp_path)

        assert result is False
