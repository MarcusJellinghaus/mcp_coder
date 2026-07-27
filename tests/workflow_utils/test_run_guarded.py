"""Tests for the shared ``run_guarded`` safety-net runner."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflow_utils.failure_handling import GuardOutcome, run_guarded

PROJECT_DIR = Path("/fake/project")


def _run(body: object, **overrides: object) -> int:
    """Invoke run_guarded with sensible defaults for the guard metadata."""
    kwargs: dict[str, object] = {
        "project_dir": PROJECT_DIR,
        "from_label_id": "busy",
        "general_category": "general_failed",
        "comment_header": "**Workflow failed unexpectedly.**",
    }
    kwargs.update(overrides)
    return run_guarded(body, **kwargs)  # type: ignore[arg-type]


class TestRunGuardedCleanReturn:
    """A clean return from body() is terminal; the net stays silent."""

    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_body_returns_zero_is_silent(self, mock_handle: MagicMock) -> None:
        result = _run(lambda: 0)

        assert result == 0
        mock_handle.assert_not_called()

    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_body_returns_one_is_silent(self, mock_handle: MagicMock) -> None:
        result = _run(lambda: 1)

        assert result == 1
        mock_handle.assert_not_called()


class TestRunGuardedException:
    """An unexpected exception is netted and mapped to the general label."""

    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_generic_exception_nets_and_returns_one(
        self, mock_handle: MagicMock
    ) -> None:
        def body() -> int:
            raise ValueError("boom")

        result = _run(body)

        assert result == 1
        mock_handle.assert_called_once()
        failure = mock_handle.call_args.args[0]
        comment = mock_handle.call_args.args[1]
        assert failure.category == "general_failed"
        assert "**Workflow failed unexpectedly.**" in comment

    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_mcp_unavailable_names_servers(self, mock_handle: MagicMock) -> None:
        def body() -> int:
            raise McpServersUnavailableError("boom", {"mcp-tools-py": "failed"})

        result = _run(body)

        assert result == 1
        mock_handle.assert_called_once()
        failure = mock_handle.call_args.args[0]
        comment = mock_handle.call_args.args[1]
        assert failure.category == "general_failed"
        assert "mcp-tools-py (failed)" in failure.message
        assert "mcp-tools-py (failed)" in comment


class TestRunGuardedSystemExit:
    """SystemExit is netted then re-raised (SIGTERM parity)."""

    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_sys_exit_nets_and_reraises(self, mock_handle: MagicMock) -> None:
        def body() -> int:
            raise SystemExit(1)

        with pytest.raises(SystemExit):
            _run(body)

        mock_handle.assert_called_once()
        failure = mock_handle.call_args.args[0]
        assert failure.category == "general_failed"
        assert failure.stage == "Unexpected exit"

    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_sigterm_handler_marks_signal_stage(self, mock_handle: MagicMock) -> None:
        """Body triggers the installed SIGTERM handler, then SystemExit escapes."""
        import signal

        def body() -> int:
            handler = signal.getsignal(signal.SIGTERM)
            assert callable(handler)
            handler(signal.SIGTERM, None)  # sets sigterm flag and sys.exit(1)
            return 0

        with pytest.raises(SystemExit):
            _run(body)

        mock_handle.assert_called_once()
        failure = mock_handle.call_args.args[0]
        comment = mock_handle.call_args.args[1]
        assert failure.stage == "SIGTERM received"
        assert "terminated by signal" in failure.message
        assert "terminated by signal" in comment


class TestRunGuardedBuildComment:
    """A build_comment closure reads the live outcome at net time."""

    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_build_comment_reflects_live_mutation(self, mock_handle: MagicMock) -> None:
        holder = {"progress": "0/3"}

        def build_comment(outcome: GuardOutcome) -> str:
            return f"Progress: {holder['progress']} | stage={outcome.stage}"

        def body() -> int:
            holder["progress"] = "2/3"
            raise ValueError("boom")

        result = _run(body, build_comment=build_comment)

        assert result == 1
        comment = mock_handle.call_args.args[1]
        assert "Progress: 2/3" in comment
