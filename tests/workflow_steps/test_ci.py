"""Tests for the CI check-and-fix workflow step (workflow_steps/ci.py)."""

import logging
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.checks.branch_status import truncate_ci_details
from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflow_steps.ci import (
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

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO, logger="mcp_coder.workflow_steps.ci"):
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

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO, logger="mcp_coder.workflow_steps.ci"):
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

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.DEBUG, logger="mcp_coder.workflow_steps.ci"):
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

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.DEBUG, logger="mcp_coder.workflow_steps.ci"):
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

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO, logger="mcp_coder.workflow_steps.ci"):
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


class TestDefaultPromptHeaders:
    """Characterization: default headers reach get_prompt_with_substitutions."""

    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch("mcp_coder.workflow_steps.ci.get_prompt_with_substitutions")
    def test_analysis_uses_default_header(
        self,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store: MagicMock,
    ) -> None:
        """The analysis phase loads the "CI Failure Analysis Prompt" header."""
        mock_get_prompt.return_value = "analysis prompt"
        mock_prompt_llm.return_value = {"text": "analysis response"}

        _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

        header = mock_get_prompt.call_args.args[1]
        assert header == "CI Failure Analysis Prompt"

    @patch("mcp_coder.workflow_steps.ci.push_changes", return_value=True)
    @patch("mcp_coder.workflow_steps.ci.commit_changes", return_value=True)
    @patch("mcp_coder.workflow_steps.ci.run_formatters", return_value=True)
    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch("mcp_coder.workflow_steps.ci.get_prompt_with_substitutions")
    def test_fix_uses_default_header(
        self,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store: MagicMock,
        _mock_format: MagicMock,
        _mock_commit: MagicMock,
        _mock_push: MagicMock,
    ) -> None:
        """The fix phase loads the "CI Fix Prompt" header."""
        mock_get_prompt.return_value = "fix prompt"
        mock_prompt_llm.return_value = {"text": "fix response"}

        _run_ci_fix(_make_config(), "problem", fix_attempt=0)

        header = mock_get_prompt.call_args.args[1]
        assert header == "CI Fix Prompt"


class TestDefaultSessionDir:
    """Characterization: sessions stored under .mcp-coder/implement_sessions."""

    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch("mcp_coder.workflow_steps.ci.get_prompt_with_substitutions")
    def test_analysis_session_dir(
        self,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store: MagicMock,
    ) -> None:
        """Analysis sessions are stored under .mcp-coder/implement_sessions."""
        mock_get_prompt.return_value = "analysis prompt"
        mock_prompt_llm.return_value = {"text": "analysis response"}

        _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

        store_path = mock_store.call_args.kwargs["store_path"]
        assert store_path.endswith(str(Path(".mcp-coder") / "implement_sessions"))


class TestRunCiAnalysisPropagatesLlmFailures:
    """_run_ci_analysis re-raises the two typed LLM failures (Decision 9)."""

    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
        return_value="analysis prompt",
    )
    def test_llm_timeout_propagates(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """LLMTimeoutError is NOT swallowed to None; it propagates out."""
        mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

        with pytest.raises(LLMTimeoutError):
            _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
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
        "mcp_coder.workflow_steps.ci.prompt_llm",
        side_effect=RuntimeError("boom"),
    )
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
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

    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
        return_value="fix prompt",
    )
    def test_llm_timeout_absorbed_as_false(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """LLMTimeoutError becomes a single failed attempt (return False)."""
        mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

        result = _run_ci_fix(_make_config(), "problem", fix_attempt=0)
        assert result is False

    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
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


class TestTruncateCiDetails:
    """Tests for truncate_ci_details function (shared truncation logic)."""

    def test_short_log_returned_unchanged(self) -> None:
        """Logs under 300 lines should be returned as-is."""
        log = "\n".join([f"Line {i}" for i in range(200)])

        result = truncate_ci_details(log)

        assert result == log

    def test_exactly_300_lines_returned_unchanged(self) -> None:
        """Logs of exactly 300 lines should be returned as-is."""
        log = "\n".join([f"Line {i}" for i in range(300)])

        result = truncate_ci_details(log)

        assert result == log

    def test_long_log_truncated_to_first_10_last_290(self) -> None:
        """Logs over 300 lines should have first 10 + last 290 lines."""
        log = "\n".join([f"Line {i}" for i in range(400)])

        result = truncate_ci_details(log)

        # Should have 300 lines + truncation marker
        assert "Line 0" in result  # First line preserved
        assert "Line 9" in result  # Line 10 preserved (0-indexed)
        assert "Line 399" in result  # Last line preserved
        assert "Line 110" in result  # From last 290 (400-290=110)
        assert "Line 10" not in result  # Should be truncated
        assert "Line 109" not in result  # Should be truncated
        assert "..." in result or "[truncated]" in result.lower()

    def test_empty_log_returns_empty(self) -> None:
        """Empty log should return empty string."""
        result = truncate_ci_details("")

        assert result == ""
