"""Tests for implement workflow SIGTERM handling (owned by run_guarded).

Split out of test_core_workflow.py, which sits close to the CI file-size gate
(`mcp-coder check file-size --max-lines 750`).
"""

import signal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.implement.core import run_implement_workflow
from mcp_coder.workflows.implement.task_tracker_prep import TrackerPrepError

# Patch targets for the two failure boundaries after the run_guarded migration:
# - deliberate in-body failures go through implement's `_fail` -> this handler
_DELIBERATE_HANDLER = (
    "mcp_coder.workflows.implement.failure_reporting.handle_workflow_failure"
)
# - the SIGTERM / unexpected-exit safety net lives in run_guarded -> this handler
_NET_HANDLER = "mcp_coder.workflow_utils.failure_handling.handle_workflow_failure"
# run_guarded installs/restores the SIGTERM handler via the signal module here
_NET_SIGNAL = "mcp_coder.workflow_utils.failure_handling.signal.signal"


class TestSigtermHandler:
    """Tests for SIGTERM handler registration and behavior (owned by run_guarded)."""

    @patch(_NET_SIGNAL)
    @patch(_DELIBERATE_HANDLER)
    @patch(
        "mcp_coder.workflows.implement.core.prepare_task_tracker",
        side_effect=TrackerPrepError("task_tracker_prep_failed", "prep failed"),
    )
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_sigterm_handler_registered(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """SIGTERM handler is registered by run_guarded after prereq checks pass."""
        run_implement_workflow(Path("/fake"), "claude")

        sigterm_calls = [
            c for c in mock_signal.call_args_list if c[0][0] == signal.SIGTERM
        ]
        assert len(sigterm_calls) >= 1

    @patch(_NET_SIGNAL)
    @patch(_DELIBERATE_HANDLER)
    @patch(
        "mcp_coder.workflows.implement.core.prepare_task_tracker",
        side_effect=TrackerPrepError("task_tracker_prep_failed", "prep failed"),
    )
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_sigterm_handler_restored_in_finally(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prepare: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """Previous SIGTERM handler is restored after run_guarded completes."""
        original_handler = MagicMock()
        mock_signal.return_value = original_handler

        run_implement_workflow(Path("/fake"), "claude")

        final_call = mock_signal.call_args_list[-1]
        assert final_call[0][0] == signal.SIGTERM
        assert final_call[0][1] == original_handler

    @patch(_NET_SIGNAL)
    @patch(_NET_HANDLER)
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True)
    @patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True)
    def test_sigterm_sets_flag_and_exits(
        self,
        mock_git_clean: MagicMock,
        mock_main_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_rebase: MagicMock,
        mock_prep: MagicMock,
        mock_handle: MagicMock,
        mock_signal: MagicMock,
    ) -> None:
        """SIGTERM handler sets its flag and the net reports 'SIGTERM received'."""
        # Capture the handler run_guarded registers.
        handlers: dict[int, Any] = {}

        def capture_handler(sig: int, handler: Any) -> Any:
            handlers[sig] = handler
            return signal.SIG_DFL

        mock_signal.side_effect = capture_handler

        # Make prepare_task_tracker call the registered SIGTERM handler.
        def trigger_sigterm(*args: Any, **kwargs: Any) -> None:
            handler = handlers.get(signal.SIGTERM)
            if handler:
                with pytest.raises(SystemExit):
                    handler(signal.SIGTERM, None)
            raise SystemExit(1)

        mock_prep.side_effect = trigger_sigterm

        with pytest.raises(SystemExit):
            run_implement_workflow(Path("/fake"), "claude")

        # The net should have reported the SIGTERM-driven exit.
        mock_handle.assert_called()
        failure = mock_handle.call_args[0][0]
        assert failure.stage == "SIGTERM received"
        assert failure.message == "Workflow terminated by signal"
