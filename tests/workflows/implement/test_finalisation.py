"""Tests for implement workflow finalisation stage."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from mcp_coder.workflow_utils.task_tracker import TaskTrackerFileNotFoundError
from mcp_coder.workflows.implement.finalisation import run_finalisation


# Reusable LLMResponseDict mock value
def _make_llm_response(text: str = "LLM response text") -> Dict[str, Any]:
    return {
        "text": text,
        "session_id": "test-session",
        "version": "1.0",
        "timestamp": "2025-01-01T00:00:00",
        "provider": "claude",
        "raw_response": {},
    }


class TestRunFinalisation:
    """Tests for run_finalisation function."""

    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_skips_when_no_incomplete_tasks(
        self, mock_has_incomplete: MagicMock, tmp_path: Path
    ) -> None:
        """Test run_finalisation skips LLM call when no incomplete tasks."""
        mock_has_incomplete.return_value = False

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_has_incomplete.assert_called_once_with(str(tmp_path / "pr_info"))

    @patch("mcp_coder.workflows.implement.finalisation.get_full_status")
    @patch("mcp_coder.workflows.implement.finalisation.store_session")
    @patch("mcp_coder.workflows.implement.finalisation.prompt_llm")
    @patch("mcp_coder.workflows.implement.finalisation.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_calls_llm_when_incomplete_tasks(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation calls LLM when there are incomplete tasks."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        # No changes after LLM call
        mock_get_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": [],
        }

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_prompt_llm.assert_called_once()
        # Verify the prompt contains key finalisation instructions
        call_args = mock_prompt_llm.call_args
        prompt = call_args[0][0] if call_args[0] else call_args[1].get("question", "")
        assert "TASK_TRACKER.md" in prompt
        assert "unchecked tasks" in prompt
        # Verify store_session called with finalisation step_name
        mock_store_session.assert_called_once()
        store_call_kwargs = mock_store_session.call_args[1]
        assert store_call_kwargs.get("step_name") == "finalisation"

    @patch("mcp_coder.workflows.implement.finalisation.push_changes")
    @patch("mcp_coder.workflows.implement.finalisation.commit_all_changes")
    @patch("mcp_coder.workflows.implement.finalisation.get_full_status")
    @patch("mcp_coder.workflows.implement.finalisation.store_session")
    @patch("mcp_coder.workflows.implement.finalisation.prompt_llm")
    @patch("mcp_coder.workflows.implement.finalisation.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_commits_and_pushes_when_changes_exist(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation commits and pushes changes when they exist."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = True

        # Create commit message file
        pr_info_dir = tmp_path / "pr_info"
        pr_info_dir.mkdir(parents=True)
        commit_msg_file = pr_info_dir / ".commit_message.txt"
        commit_msg_file.write_text("Test commit message")

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_commit.assert_called_once_with("Test commit message", tmp_path)
        mock_push.assert_called_once_with(tmp_path)
        # Verify commit message file was deleted
        assert not commit_msg_file.exists()

    @patch("mcp_coder.workflows.implement.finalisation.push_changes")
    @patch("mcp_coder.workflows.implement.finalisation.commit_all_changes")
    @patch(
        "mcp_coder.workflows.implement.finalisation.generate_commit_message_with_llm"
    )
    @patch("mcp_coder.workflows.implement.finalisation.get_full_status")
    @patch("mcp_coder.workflows.implement.finalisation.store_session")
    @patch("mcp_coder.workflows.implement.finalisation.prompt_llm")
    @patch("mcp_coder.workflows.implement.finalisation.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_uses_llm_generated_message_when_file_missing(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_generate_commit_msg: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation uses LLM-generated message when commit file missing."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        # LLM generates commit message successfully
        mock_generate_commit_msg.return_value = (
            True,
            "LLM generated commit message",
            None,
        )
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = True

        # Don't create commit message file - should fall back to LLM

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_generate_commit_msg.assert_called_once()
        mock_commit.assert_called_once_with("LLM generated commit message", tmp_path)
        mock_push.assert_called_once_with(tmp_path)

    @patch("mcp_coder.workflows.implement.finalisation.push_changes")
    @patch("mcp_coder.workflows.implement.finalisation.commit_all_changes")
    @patch(
        "mcp_coder.workflows.implement.finalisation.generate_commit_message_with_llm"
    )
    @patch("mcp_coder.workflows.implement.finalisation.get_full_status")
    @patch("mcp_coder.workflows.implement.finalisation.store_session")
    @patch("mcp_coder.workflows.implement.finalisation.prompt_llm")
    @patch("mcp_coder.workflows.implement.finalisation.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_uses_default_message_when_llm_fails(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_generate_commit_msg: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation uses default message when both file and LLM fail."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        # LLM fails to generate commit message
        mock_generate_commit_msg.return_value = (False, "", "LLM error")
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = True

        # Don't create commit message file - LLM also fails - should use default

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        mock_generate_commit_msg.assert_called_once()
        mock_commit.assert_called_once_with(
            "Finalisation: complete remaining tasks", tmp_path
        )
        mock_push.assert_called_once_with(tmp_path)

    @patch("mcp_coder.workflows.implement.finalisation.get_full_status")
    @patch("mcp_coder.workflows.implement.finalisation.store_session")
    @patch("mcp_coder.workflows.implement.finalisation.prompt_llm")
    @patch("mcp_coder.workflows.implement.finalisation.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_no_commit_when_no_changes(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation skips commit when no changes after LLM."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": [],
        }

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        # No commit or push should be called

    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_returns_false_when_task_tracker_missing(
        self, mock_has_incomplete: MagicMock, tmp_path: Path
    ) -> None:
        """Test run_finalisation returns False when task tracker is missing."""
        mock_has_incomplete.side_effect = TaskTrackerFileNotFoundError(
            "TASK_TRACKER.md not found"
        )

        result = run_finalisation(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.finalisation.store_session")
    @patch("mcp_coder.workflows.implement.finalisation.prompt_llm")
    @patch("mcp_coder.workflows.implement.finalisation.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_returns_false_on_empty_llm_response(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation returns False when LLM returns empty response."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("")  # Empty text

        result = run_finalisation(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.finalisation.commit_all_changes")
    @patch("mcp_coder.workflows.implement.finalisation.get_full_status")
    @patch("mcp_coder.workflows.implement.finalisation.store_session")
    @patch("mcp_coder.workflows.implement.finalisation.prompt_llm")
    @patch("mcp_coder.workflows.implement.finalisation.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_returns_false_when_commit_fails(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation returns False when commit fails."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": False, "error": "Commit failed"}

        result = run_finalisation(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.finalisation.push_changes")
    @patch("mcp_coder.workflows.implement.finalisation.commit_all_changes")
    @patch("mcp_coder.workflows.implement.finalisation.get_full_status")
    @patch("mcp_coder.workflows.implement.finalisation.store_session")
    @patch("mcp_coder.workflows.implement.finalisation.prompt_llm")
    @patch("mcp_coder.workflows.implement.finalisation.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_returns_false_when_push_fails(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation returns False when push fails."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_get_status.return_value = {
            "staged": [],
            "modified": ["some_file.py"],
            "untracked": [],
        }
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = False

        result = run_finalisation(tmp_path, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.finalisation.get_full_status")
    @patch("mcp_coder.workflows.implement.finalisation.store_session")
    @patch("mcp_coder.workflows.implement.finalisation.prompt_llm")
    @patch("mcp_coder.workflows.implement.finalisation.prepare_llm_environment")
    @patch("mcp_coder.workflows.implement.finalisation.has_incomplete_work")
    def test_run_finalisation_store_session_failure_is_non_critical(
        self,
        mock_has_incomplete: MagicMock,
        mock_prepare_env: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run_finalisation succeeds even when store_session raises."""
        mock_has_incomplete.return_value = True
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm.return_value = _make_llm_response("Finalisation completed")
        mock_store_session.side_effect = Exception("Storage failure")
        mock_get_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": [],
        }

        # Should still succeed even though store_session raises
        result = run_finalisation(tmp_path, "claude")

        assert result is True
