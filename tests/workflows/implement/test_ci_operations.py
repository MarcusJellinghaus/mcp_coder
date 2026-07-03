"""Tests for CI operations (ci_operations.py)."""

import logging
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflows.implement.ci_operations import (
    CIFixConfig,
    _poll_for_ci_completion,
    _run_ci_analysis,
    _run_ci_fix,
)


class TestPollForCiCompletionHeartbeat:
    """Tests for elapsed time and heartbeat logging in _poll_for_ci_completion."""

    def test_heartbeat_logged_at_interval(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """INFO heartbeat is logged every 8 iterations."""
        mock_ci_manager = MagicMock()
        in_progress: Dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        # 9 in-progress responses, then completed on 10th
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 9 + [
            completed
        ]

        with patch("mcp_coder.workflows.implement.ci_operations.time.sleep"):
            with caplog.at_level(
                logging.INFO, logger="mcp_coder.workflows.implement.ci_operations"
            ):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [
            r for r in caplog.records if "CI polling heartbeat" in r.message
        ]
        assert len(heartbeat_logs) == 1  # Fires at iteration 8

    def test_no_heartbeat_before_interval(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No heartbeat logged when fewer than 8 iterations complete."""
        mock_ci_manager = MagicMock()
        in_progress: Dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        # Only 5 in-progress, then completed
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 5 + [
            completed
        ]

        with patch("mcp_coder.workflows.implement.ci_operations.time.sleep"):
            with caplog.at_level(
                logging.INFO, logger="mcp_coder.workflows.implement.ci_operations"
            ):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [
            r for r in caplog.records if "CI polling heartbeat" in r.message
        ]
        assert len(heartbeat_logs) == 0

    def test_elapsed_time_in_debug_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """Debug logs include elapsed time."""
        mock_ci_manager = MagicMock()
        in_progress: Dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress, completed]

        with patch("mcp_coder.workflows.implement.ci_operations.time.sleep"):
            with caplog.at_level(
                logging.DEBUG, logger="mcp_coder.workflows.implement.ci_operations"
            ):
                _poll_for_ci_completion(mock_ci_manager, "main")

        debug_logs = [
            r
            for r in caplog.records
            if "elapsed" in r.message.lower() and "in progress" in r.message.lower()
        ]
        assert len(debug_logs) >= 1

    def test_elapsed_time_in_no_run_found_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """'No CI run found yet' debug logs include elapsed time."""
        mock_ci_manager = MagicMock()
        empty_status: Dict[str, Any] = {"run": {}, "jobs": []}
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        mock_ci_manager.get_latest_ci_status.side_effect = [empty_status, completed]

        with patch("mcp_coder.workflows.implement.ci_operations.time.sleep"):
            with caplog.at_level(
                logging.DEBUG, logger="mcp_coder.workflows.implement.ci_operations"
            ):
                _poll_for_ci_completion(mock_ci_manager, "main")

        no_run_logs = [
            r
            for r in caplog.records
            if "no ci run found" in r.message.lower() and "elapsed" in r.message.lower()
        ]
        assert len(no_run_logs) >= 1

    def test_multiple_heartbeats_at_16_iterations(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Two heartbeats logged at iterations 8 and 16."""
        mock_ci_manager = MagicMock()
        in_progress: Dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: Dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 17 + [
            completed
        ]

        with patch("mcp_coder.workflows.implement.ci_operations.time.sleep"):
            with caplog.at_level(
                logging.INFO, logger="mcp_coder.workflows.implement.ci_operations"
            ):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [
            r for r in caplog.records if "CI polling heartbeat" in r.message
        ]
        assert len(heartbeat_logs) == 2  # Fires at iterations 8 and 16


def _make_config() -> CIFixConfig:
    """Build a minimal CIFixConfig for exercising the analysis/fix helpers."""
    return CIFixConfig(
        project_dir=Path("/test/project"),
        provider="claude",
        env_vars={},
        cwd="/test/project",
        mcp_config=None,
        settings_file=None,
    )


def _make_failed_summary() -> Dict[str, Any]:
    """Build a minimal failed-jobs summary for _run_ci_analysis."""
    return {
        "job_name": "build",
        "step_name": "pytest",
        "other_failed_jobs": [],
        "log_excerpt": "some failing log",
    }


class TestRunCiAnalysisPropagatesLlmFailures:
    """_run_ci_analysis re-raises the two typed LLM failures (Decision 9)."""

    @patch("mcp_coder.workflows.implement.ci_operations.prompt_llm")
    @patch(
        "mcp_coder.workflows.implement.ci_operations.get_prompt_with_substitutions",
        return_value="analysis prompt",
    )
    def test_llm_timeout_propagates(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """LLMTimeoutError is NOT swallowed to None; it propagates out."""
        mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

        with pytest.raises(LLMTimeoutError):
            _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

    @patch("mcp_coder.workflows.implement.ci_operations.prompt_llm")
    @patch(
        "mcp_coder.workflows.implement.ci_operations.get_prompt_with_substitutions",
        return_value="analysis prompt",
    )
    def test_mcp_unavailable_propagates(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """McpServersUnavailableError is NOT swallowed to None; it propagates out."""
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        with pytest.raises(McpServersUnavailableError):
            _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

    @patch(
        "mcp_coder.workflows.implement.ci_operations.prompt_llm",
        side_effect=RuntimeError("boom"),
    )
    @patch(
        "mcp_coder.workflows.implement.ci_operations.get_prompt_with_substitutions",
        return_value="analysis prompt",
    )
    def test_generic_exception_still_soft_fails(
        self, _mock_prompt: MagicMock, _mock_prompt_llm: MagicMock
    ) -> None:
        """A generic exception is still soft-swallowed to None (unchanged)."""
        result = _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)
        assert result is None


class TestRunCiFixAbsorbsLlmFailures:
    """_run_ci_fix absorbs the two typed LLM failures into one failed attempt."""

    @patch("mcp_coder.workflows.implement.ci_operations.prompt_llm")
    @patch(
        "mcp_coder.workflows.implement.ci_operations.get_prompt_with_substitutions",
        return_value="fix prompt",
    )
    def test_llm_timeout_absorbed_as_false(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """LLMTimeoutError becomes a single failed attempt (return False)."""
        mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

        result = _run_ci_fix(_make_config(), "problem", fix_attempt=0)
        assert result is False

    @patch("mcp_coder.workflows.implement.ci_operations.prompt_llm")
    @patch(
        "mcp_coder.workflows.implement.ci_operations.get_prompt_with_substitutions",
        return_value="fix prompt",
    )
    def test_mcp_unavailable_absorbed_as_false(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """McpServersUnavailableError becomes a single failed attempt (return False)."""
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        result = _run_ci_fix(_make_config(), "problem", fix_attempt=0)
        assert result is False
