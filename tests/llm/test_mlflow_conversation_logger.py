"""Tests for MLflow conversation context manager (two-phase logging)."""

import json
import logging
from typing import Any, Generator
from unittest.mock import MagicMock, call, patch

import pytest

from mcp_coder.llm.mlflow_conversation_logger import mlflow_conversation


class TestMlflowConversationHappyPath:
    """Test normal operation of the context manager."""

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_phase1_logs_prompt_phase2_logs_response(
        self, mock_get_logger: Any
    ) -> None:
        """Happy path: Phase 1 logs prompt artifact, Phase 2 logs conversation and ends FINISHED."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = False
        mock_logger.current_step.return_value = 0
        mock_get_logger.return_value = mock_logger

        response_data = {"text": "hello", "session_id": "sid-1", "provider": "claude"}

        with mlflow_conversation(
            prompt="What is Python?",
            provider="claude",
            session_id=None,
            metadata={"model": "claude-3"},
        ) as result:
            # Verify Phase 1 happened: start_run and log_artifact called
            mock_logger.start_run.assert_called_once()
            mock_logger.log_artifact.assert_called_once_with(
                "What is Python?", "step_0_prompt.txt"
            )
            # Caller sets response_data
            result["response_data"] = response_data

        # Verify Phase 2: log_conversation called with prompt and response
        mock_logger.log_conversation.assert_called_once_with(
            "What is Python?", response_data, {"model": "claude-3"}
        )
        mock_logger.end_run.assert_called_once_with("FINISHED", session_id="sid-1")

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_run_name_new_session(self, mock_get_logger: Any) -> None:
        """Run name includes 'new' when no existing session."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = False
        mock_logger.current_step.return_value = 0
        mock_get_logger.return_value = mock_logger

        with mlflow_conversation(prompt="hi", provider="claude") as result:
            result["response_data"] = {"text": "ok", "provider": "claude"}

        call_kwargs = mock_logger.start_run.call_args[1]
        assert "new" in call_kwargs["run_name"]


class TestMlflowConversationErrorPath:
    """Test error handling in the context manager."""

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_exception_during_yield_logs_error_and_ends_failed(
        self, mock_get_logger: Any
    ) -> None:
        """Exception during yield → Phase 2 logs error + ends run FAILED."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = False
        mock_logger.current_step.return_value = 0
        mock_get_logger.return_value = mock_logger

        with pytest.raises(ValueError, match="boom"):
            with mlflow_conversation(
                prompt="fail me", provider="claude", session_id="sid-x"
            ) as _result:
                raise ValueError("boom")

        mock_logger.log_error_metrics.assert_called_once()
        error_arg = mock_logger.log_error_metrics.call_args[0][0]
        assert isinstance(error_arg, ValueError)
        mock_logger.end_run.assert_called_once_with("FAILED", session_id="sid-x")


class TestMlflowConversationDisabled:
    """Test no-op behavior when MLflow is disabled or not installed."""

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_disabled_is_noop(self, mock_get_logger: Any) -> None:
        """When MLflow is disabled, context manager yields normally without logging."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = False
        mock_get_logger.return_value = mock_logger

        with mlflow_conversation(prompt="test", provider="claude") as result:
            assert result["response_data"] is None
            result["response_data"] = {"text": "ok"}

        mock_logger.start_run.assert_not_called()
        mock_logger.log_artifact.assert_not_called()
        mock_logger.log_conversation.assert_not_called()
        mock_logger.end_run.assert_not_called()

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_not_installed_is_noop(self, mock_get_logger: Any) -> None:
        """When MLflow not installed (_is_enabled returns False), context manager is no-op."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = False
        mock_get_logger.return_value = mock_logger

        with mlflow_conversation(prompt="test", provider="langchain") as result:
            result["response_data"] = {"text": "response"}

        mock_logger.start_run.assert_not_called()


class TestMlflowConversationSessionReuse:
    """Test session reuse behavior."""

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_session_reuse_run_name(self, mock_get_logger: Any) -> None:
        """Passing known session_id → run_name contains 'resuming'."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = True
        mock_logger.current_step.return_value = 0
        mock_get_logger.return_value = mock_logger

        with mlflow_conversation(
            prompt="hi again", provider="claude", session_id="sid-existing"
        ) as result:
            result["response_data"] = {
                "text": "ok",
                "session_id": "sid-existing",
                "provider": "claude",
            }

        call_kwargs = mock_logger.start_run.call_args[1]
        assert "resuming" in call_kwargs["run_name"]
        assert call_kwargs["session_id"] == "sid-existing"

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_resumed_session_uses_step_1_prompt_artifact(
        self, mock_get_logger: Any
    ) -> None:
        """When resuming a session at step 1, Phase 1 artifact is step_1_prompt.txt."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = True
        mock_logger.current_step.return_value = 1
        mock_get_logger.return_value = mock_logger

        with mlflow_conversation(
            prompt="hi", provider="claude", session_id="sid-x"
        ) as result:
            result["response_data"] = {
                "text": "ok",
                "session_id": "sid-x",
                "provider": "claude",
            }

        # Phase 1 artifact should be step_1_prompt.txt
        mock_logger.log_artifact.assert_any_call("hi", "step_1_prompt.txt")


class TestMlflowConversationPhase2Failure:
    """Test that Phase 2 failures are swallowed with a warning."""

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_phase2_failure_logs_warning_no_exception(
        self, mock_get_logger: Any
    ) -> None:
        """If Phase 2 logging itself fails, warning is logged but no exception raised."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = False
        mock_logger.current_step.return_value = 0
        mock_logger.log_conversation.side_effect = RuntimeError("mlflow down")
        mock_get_logger.return_value = mock_logger

        with patch(
            "mcp_coder.llm.mlflow_conversation_logger.logger"
        ) as mock_module_logger:
            # Should NOT raise
            with mlflow_conversation(prompt="test", provider="claude") as result:
                result["response_data"] = {"text": "ok", "provider": "claude"}

            mock_module_logger.warning.assert_called_once()
            assert "Phase 2" in mock_module_logger.warning.call_args[0][0]


class TestMlflowConversationKilledPath:
    """Test behavior when no response and no error (process killed mid-yield)."""

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_no_response_no_error_ends_killed(self, mock_get_logger: Any) -> None:
        """When yield exits normally but no response_data set, end run as KILLED."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = False
        mock_logger.current_step.return_value = 0
        mock_get_logger.return_value = mock_logger

        with mlflow_conversation(
            prompt="test", provider="claude", session_id="sid-k"
        ) as _result:
            pass  # Caller never sets response_data

        mock_logger.log_conversation.assert_not_called()
        mock_logger.end_run.assert_called_once_with("KILLED", session_id="sid-k")


class TestMlflowConversationToolTrace:
    """Test tool_trace artifact logging in Phase 2."""

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_tool_trace_logged_as_artifact(self, mock_get_logger: Any) -> None:
        """When raw_response contains tool_trace, it is logged as tool_trace.json artifact."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = False
        mock_logger.current_step.return_value = 0
        mock_get_logger.return_value = mock_logger

        tool_trace = [
            {"name": "read_file", "args": {"path": "a.py"}, "result": "content"},
        ]
        response_data = {
            "text": "done",
            "session_id": "sid-t",
            "provider": "langchain",
            "raw_response": {"tool_trace": tool_trace, "backend": "openai"},
        }

        with mlflow_conversation(
            prompt="test", provider="langchain", session_id="sid-t"
        ) as result:
            result["response_data"] = response_data

        # prompt.txt artifact + tool_trace.json artifact
        artifact_calls = mock_logger.log_artifact.call_args_list
        assert len(artifact_calls) == 2
        assert artifact_calls[0] == call("test", "step_0_prompt.txt")
        # Verify tool_trace.json content
        trace_content = artifact_calls[1][0][0]
        assert artifact_calls[1][0][1] == "tool_trace.json"
        assert json.loads(trace_content) == tool_trace

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_no_tool_trace_artifact_when_absent(self, mock_get_logger: Any) -> None:
        """When raw_response has no tool_trace, no extra artifact is logged."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = False
        mock_logger.current_step.return_value = 0
        mock_get_logger.return_value = mock_logger

        response_data = {
            "text": "done",
            "session_id": "sid-n",
            "provider": "claude",
            "raw_response": {"backend": "openai"},
        }

        with mlflow_conversation(
            prompt="test", provider="claude", session_id="sid-n"
        ) as result:
            result["response_data"] = response_data

        # Only prompt.txt artifact, no tool_trace.json
        artifact_calls = mock_logger.log_artifact.call_args_list
        assert len(artifact_calls) == 1
        assert artifact_calls[0] == call("test", "step_0_prompt.txt")

    @patch("mcp_coder.llm.mlflow_conversation_logger.get_mlflow_logger")
    def test_no_tool_trace_artifact_when_empty_list(self, mock_get_logger: Any) -> None:
        """When tool_trace is an empty list, no artifact is logged."""
        mock_logger = MagicMock()
        mock_logger._is_enabled.return_value = True
        mock_logger.has_session.return_value = False
        mock_logger.current_step.return_value = 0
        mock_get_logger.return_value = mock_logger

        response_data = {
            "text": "done",
            "session_id": "sid-e",
            "provider": "langchain",
            "raw_response": {"tool_trace": [], "backend": "openai"},
        }

        with mlflow_conversation(
            prompt="test", provider="langchain", session_id="sid-e"
        ) as result:
            result["response_data"] = response_data

        # Only step_0_prompt.txt artifact
        artifact_calls = mock_logger.log_artifact.call_args_list
        assert len(artifact_calls) == 1
        assert artifact_calls[0] == call("test", "step_0_prompt.txt")
