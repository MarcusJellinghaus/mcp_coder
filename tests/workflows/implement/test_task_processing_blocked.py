from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.workflow_steps.constants import BLOCKED_FILE
from mcp_coder.workflows.implement.constants import (
    BLOCKED_FILE as IMPLEMENT_BLOCKED_FILE,
)
from mcp_coder.workflows.implement.task_processing import (
    BLOCKED_REASON_FALLBACK,
    BLOCKED_REASON_MAX_CHARS,
    RETRY_REMINDER,
    TaskOutcome,
    process_single_task,
    process_task_with_retry,
    read_and_clear_blocked,
)
from tests.workflows.implement.test_task_processing import _make_llm_response


class TestProcessSingleTaskBlocked:
    """Test pr_info/.blocked.txt detection inside process_single_task."""

    @staticmethod
    def _write_marker(project_dir: Path, text: str) -> Path:
        """Create the blocked marker with the given text and return its path."""
        (project_dir / "pr_info").mkdir(exist_ok=True)
        marker = project_dir / BLOCKED_FILE
        marker.write_text(text, encoding="utf-8")
        return marker

    @classmethod
    def _llm_writes_marker(
        cls, project_dir: Path, text: str, raises: Exception | None = None
    ) -> Callable[..., dict[str, object]]:
        """Build a prompt_llm side effect that drops the marker mid-call.

        The agent writes the marker during its turn, so a marker created before
        process_single_task runs would be swept by the start-of-task cleanup.
        """

        def _side_effect(*_args: Any, **_kwargs: Any) -> dict[str, object]:
            cls._write_marker(project_dir, text)
            if raises is not None:
                raise raises
            return _make_llm_response("Response")

        return _side_effect

    @patch("mcp_coder.workflows.implement.task_processing.push_changes")
    @patch("mcp_coder.workflows.implement.task_processing.commit_changes")
    @patch("mcp_coder.workflows.implement.task_processing.run_formatters")
    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_blocked_wins_over_changed_files(
        self,
        mock_get_incomplete: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        mock_run_formatters: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A marker plus changed files is blocked, never success.

        The marker file is itself an untracked change, so if the files-changed
        check ran first the run would commit the marker and report success -
        the exact inversion this feature exists to prevent.
        """
        mock_get_incomplete.return_value = ["Step 1: Test task"]
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = self._llm_writes_marker(
            tmp_path, "pytest never finishes"
        )
        mock_get_status.return_value = {
            "staged": ["f.py"],
            "modified": [],
            "untracked": [],
        }

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "blocked"
        assert outcome.detail == "pytest never finishes"
        mock_commit.assert_not_called()
        mock_push.assert_not_called()
        mock_run_formatters.assert_not_called()
        assert not (tmp_path / BLOCKED_FILE).exists()

    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_empty_marker_is_blocked_not_no_changes(
        self,
        mock_get_incomplete: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A whitespace-only marker still reports blocked, never no_changes."""
        mock_get_incomplete.return_value = ["Step 1: Test task"]
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = self._llm_writes_marker(tmp_path, "   \n\t")
        mock_get_status.return_value = {"staged": [], "modified": [], "untracked": []}

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "blocked"
        assert outcome.detail == BLOCKED_REASON_FALLBACK
        assert not (tmp_path / BLOCKED_FILE).exists()

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_marker_plus_timeout_keeps_timeout_label(
        self,
        mock_get_incomplete: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """The typed LLM failure wins the label; the marker text rides along."""
        mock_get_incomplete.return_value = ["Step 1: Test task"]
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = self._llm_writes_marker(
            tmp_path,
            "mcp server never answered",
            raises=LLMTimeoutError("timed out after 3600s"),
        )

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "timeout"
        assert "mcp server never answered" in outcome.detail
        assert not (tmp_path / BLOCKED_FILE).exists()

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_marker_plus_mcp_unavailable_keeps_mcp_label(
        self,
        mock_get_incomplete: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Same precedence for an unavailable MCP server."""
        mock_get_incomplete.return_value = ["Step 1: Test task"]
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = self._llm_writes_marker(
            tmp_path,
            "tools-py is down",
            raises=McpServersUnavailableError(
                "MCP servers unavailable",
                {"mcp-tools-py": "failed"},
            ),
        )

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "mcp_unavailable"
        assert "tools-py is down" in outcome.detail
        assert not (tmp_path / BLOCKED_FILE).exists()

    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_marker_plus_empty_response_reports_blocked(
        self,
        mock_get_incomplete: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """For the untyped 'error' paths, blocked wins over the generic label.

        The empty-response guard is a plain return inside the try body, so it
        would bypass the marker entirely if the read were not in a `finally`.
        'error' maps to the uninformative 'general' label the marker exists to
        replace, hence the opposite precedence to timeout / mcp_unavailable.
        """

        def _empty_response_with_marker(
            *_args: Any, **_kwargs: Any
        ) -> dict[str, object]:
            self._write_marker(tmp_path, "cannot verify - checks never return")
            return _make_llm_response("")

        mock_get_incomplete.return_value = ["Step 1: Test task"]
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.side_effect = _empty_response_with_marker
        mock_get_status.return_value = {"staged": [], "modified": [], "untracked": []}

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "blocked"
        assert outcome.detail == "cannot verify - checks never return"
        assert not (tmp_path / BLOCKED_FILE).exists()

    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_stale_marker_removed_at_task_start(
        self, mock_get_incomplete: MagicMock, tmp_path: Path
    ) -> None:
        """A marker left by a previous run is cleared before any work starts."""
        marker = self._write_marker(tmp_path, "left over from last run")
        mock_get_incomplete.return_value = []

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "no_tasks"
        assert not marker.exists()

    @patch("mcp_coder.workflows.implement.task_processing.get_full_status")
    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing.get_incomplete_tasks")
    def test_no_marker_still_reports_no_changes(
        self,
        mock_get_incomplete: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
        mock_get_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Regression guard: without a marker, behaviour is unchanged."""
        mock_get_incomplete.return_value = ["Step 1: Test task"]
        mock_get_prompt.return_value = "Template"
        mock_prompt_llm.return_value = _make_llm_response("Response")
        mock_get_status.return_value = {"staged": [], "modified": [], "untracked": []}

        outcome = process_single_task(tmp_path, "claude")

        assert outcome.success is False
        assert outcome.reason == "no_changes"

    @patch("mcp_coder.workflows.implement.task_processing.process_single_task")
    def test_blocked_does_not_retry(self, mock_process: MagicMock) -> None:
        """blocked is terminal - the retry wrapper returns it untouched."""
        mock_process.return_value = TaskOutcome(False, "blocked", "why")

        outcome = process_task_with_retry(Path("/test/project"), "claude")

        assert outcome.success is False
        assert outcome.reason == "blocked"
        assert outcome.detail == "why"
        assert mock_process.call_count == 1


class TestReadAndClearBlocked:
    """Test read_and_clear_blocked helper."""

    def test_returns_none_when_absent(self, tmp_path: Path) -> None:
        """No marker (and no pr_info/ dir) means 'not blocked'."""
        assert read_and_clear_blocked(tmp_path) is None

    def test_returns_text_and_deletes_file(self, tmp_path: Path) -> None:
        """A non-empty marker returns its text and is removed."""
        (tmp_path / "pr_info").mkdir()
        marker = tmp_path / BLOCKED_FILE
        marker.write_text("pytest times out", encoding="utf-8")

        assert read_and_clear_blocked(tmp_path) == "pytest times out"
        assert not marker.exists()

    def test_whitespace_only_returns_fallback(self, tmp_path: Path) -> None:
        """An empty marker still counts as blocked, never as 'no marker'."""
        (tmp_path / "pr_info").mkdir()
        marker = tmp_path / BLOCKED_FILE
        marker.write_text("   \n\t", encoding="utf-8")

        assert read_and_clear_blocked(tmp_path) == BLOCKED_REASON_FALLBACK
        assert not marker.exists()

    def test_multiline_text_collapsed_to_one_line(self, tmp_path: Path) -> None:
        """A paragraph reason arrives as one line - it becomes markdown."""
        (tmp_path / "pr_info").mkdir()
        marker = tmp_path / BLOCKED_FILE
        marker.write_text(
            "pytest times out\n\nafter 10 minutes\n\t```\n", encoding="utf-8"
        )

        assert (
            read_and_clear_blocked(tmp_path) == "pytest times out after 10 minutes ```"
        )
        assert not marker.exists()

    def test_collapse_happens_before_truncation(self, tmp_path: Path) -> None:
        """The char budget is spent on content, not on newlines.

        60 chunks of 10 x's separated by 5 newlines each. Collapsing first
        leaves 11-char units, so the 500-char budget retains 455 x's;
        truncating the raw text first would leave 15-char units and only 335.
        """
        (tmp_path / "pr_info").mkdir()
        (tmp_path / BLOCKED_FILE).write_text(
            ("\n" * 5).join("x" * 10 for _ in range(60)), encoding="utf-8"
        )

        result = read_and_clear_blocked(tmp_path)

        assert result is not None
        assert "\n" not in result
        assert result.count("x") == 455

    def test_invalid_utf8_does_not_raise(self, tmp_path: Path) -> None:
        """A non-UTF-8 marker still yields a reason and is deleted.

        UnicodeDecodeError is a ValueError, not an OSError; escaping it from
        here would replace the in-flight LLM failure at the `finally` callers.
        """
        (tmp_path / "pr_info").mkdir()
        marker = tmp_path / BLOCKED_FILE
        marker.write_bytes(b"pytest \xff\xfe times out")

        result = read_and_clear_blocked(tmp_path)

        assert result is not None
        assert "pytest" in result
        assert "times out" in result
        assert not marker.exists()

    def test_long_text_truncated(self, tmp_path: Path) -> None:
        """Overlong reasons are truncated with an ellipsis marker."""
        (tmp_path / "pr_info").mkdir()
        (tmp_path / BLOCKED_FILE).write_text("x" * 900, encoding="utf-8")

        result = read_and_clear_blocked(tmp_path)

        assert result is not None
        assert len(result) == BLOCKED_REASON_MAX_CHARS + 3
        assert result.endswith("...")

    def test_blocked_file_constant(self) -> None:
        """BLOCKED_FILE is defined in the shared tier and re-exported."""
        assert BLOCKED_FILE == "pr_info/.blocked.txt"
        assert IMPLEMENT_BLOCKED_FILE is BLOCKED_FILE


class TestBlockedExitInPrompts:
    """Test that both prompt sources offer the blocked exit."""

    def test_retry_reminder_offers_blocked_exit(self) -> None:
        """The retry reminder points at the marker instead of demanding a tick."""
        assert BLOCKED_FILE in RETRY_REMINDER
        assert "you MUST tick" not in RETRY_REMINDER

    def test_implementation_prompt_offers_blocked_exit(self) -> None:
        """The attempt-1 prompt template also offers the blocked exit."""
        prompt_template = get_prompt(
            str(PROMPTS_FILE_PATH), "Implementation Prompt Template using task tracker"
        )

        assert BLOCKED_FILE in prompt_template

    def test_complete_the_step_rule_is_conditioned(self) -> None:
        """The 'all sub-tasks [x]' gate must not contradict the blocked exit."""
        prompt_template = get_prompt(
            str(PROMPTS_FILE_PATH), "Implementation Prompt Template using task tracker"
        )

        gate = next(
            line
            for line in prompt_template.splitlines()
            if "before finishing" in line and "[x]" in line
        )
        assert "unless something blocks you" in gate

    def test_blocked_file_is_the_only_report_channel(self) -> None:
        """The blocked bullet claims exclusivity, so prose is not a report."""
        prompt_template = get_prompt(
            str(PROMPTS_FILE_PATH), "Implementation Prompt Template using task tracker"
        )

        bullet = next(b for b in prompt_template.split("\n- ") if BLOCKED_FILE in b)
        assert "ONLY" in bullet
        assert "stop and report" not in prompt_template

    def test_plan_creation_prompt_offers_blocked_exit(self) -> None:
        """Generated step preconditions must point at the marker file."""
        prompt_template = get_prompt(
            str(PROMPTS_FILE_PATH), "Implementation Plan Creation"
        )

        assert BLOCKED_FILE in prompt_template
        # The prompt quotes the phrase once, as the thing never to write.
        assert "stop and report" not in prompt_template.replace('"stop and report"', "")
