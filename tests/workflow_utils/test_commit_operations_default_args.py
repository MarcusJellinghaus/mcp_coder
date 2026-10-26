from pathlib import Path
from unittest.mock import Mock, patch

from mcp_coder.workflow_utils.commit_operations import generate_commit_message_with_llm


class TestGenerateCommitMessageWithLLM:
    """Tests for generate_commit_message_with_llm function."""

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_with_llm_success(
        self,
        mock_prompt_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test successful LLM commit message generation."""
        # Setup mocks
        mock_stage.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"
        mock_get_prompt.return_value = "Generate commit message"
        mock_prompt_llm.return_value = {
            "text": "feat: add new feature",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is True
        assert message == "feat: add new feature"
        assert error is None

        # Verify calls
        mock_stage.assert_called_once_with(project_dir)
        mock_get_diff.assert_called_once_with(project_dir)
        mock_prompt_llm.assert_called_once()

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    def test_generate_commit_message_with_llm_stage_failure(
        self, mock_stage: Mock
    ) -> None:
        """Test LLM generation with staging failure."""
        mock_stage.return_value = False

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Failed to stage changes in repository" in error_str
        assert "write permissions" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    def test_generate_commit_message_with_llm_no_changes(
        self, mock_get_diff: Mock, mock_stage: Mock
    ) -> None:
        """Test LLM generation with no changes."""
        mock_stage.return_value = True
        mock_get_diff.return_value = ""

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "No changes to commit" in error_str
        assert "modified, added, or deleted files" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_with_llm_failure(
        self,
        mock_prompt_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test LLM failure handling."""
        # Setup mocks
        mock_stage.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"
        mock_get_prompt.return_value = "Generate commit message"
        mock_prompt_llm.side_effect = Exception("LLM API error")

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM communication failed" in error_str
        assert "internet connection" in error_str


class TestGenerateCommitMessageWithLLMExtended:
    """Additional tests for the improved generate_commit_message_with_llm function."""

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    def test_stage_exception_handling(self, mock_stage: Mock) -> None:
        """Test staging operation exception handling."""
        mock_stage.side_effect = Exception("Permission denied")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Error staging changes" in error_str
        assert "Permission denied" in error_str
        assert "git repository is accessible" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    def test_git_diff_none_handling(
        self, mock_get_diff: Mock, mock_stage: Mock
    ) -> None:
        """Test git diff returning None."""
        mock_stage.return_value = True
        mock_get_diff.return_value = None

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Failed to retrieve git diff" in error_str
        assert "invalid state" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    def test_prompt_file_not_found(
        self, mock_get_prompt: Mock, mock_get_diff: Mock, mock_stage: Mock
    ) -> None:
        """Test prompt file not found error."""
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.side_effect = FileNotFoundError("prompts.md not found")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Commit prompt template not found" in error_str
        assert "prompts.md not found" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_empty_llm_response(
        self,
        mock_prompt_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test empty LLM response handling."""
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_prompt_llm.return_value = {
            "text": "",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM returned empty or null response" in error_str
        assert "AI service may be unavailable" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    @patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")
    def test_empty_parsed_commit_message(
        self,
        mock_parse: Mock,
        mock_prompt_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test empty parsed commit message handling."""
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_prompt_llm.return_value = {
            "text": "some response",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }
        mock_parse.return_value = ("", None)

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM generated an empty commit message" in error_str
        assert "AI may not have understood" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    @patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")
    def test_invalid_commit_message_format(
        self,
        mock_parse: Mock,
        mock_prompt_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test invalid commit message format handling."""
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_prompt_llm.return_value = {
            "text": "some response",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }
        # Simulate a commit message that starts with empty line (invalid)
        mock_parse.return_value = ("\n\nActual content here", None)

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM generated a commit message with empty first line" in error_str
        assert "invalid for git commits" in error_str
