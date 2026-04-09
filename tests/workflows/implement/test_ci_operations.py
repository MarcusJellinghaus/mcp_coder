"""Tests for CI operations (ci_operations.py)."""

import logging
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.implement.ci_operations import _poll_for_ci_completion


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
