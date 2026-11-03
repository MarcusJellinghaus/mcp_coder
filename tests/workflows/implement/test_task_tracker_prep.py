"""Tests for implement workflow task tracker preparation."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_utils.task_tracker import TASK_TRACKER_TEMPLATE
from mcp_coder.workflows.implement.task_tracker_prep import (
    TrackerPrepError,
    log_progress_summary,
    prepare_task_tracker,
)

PREP = "mcp_coder.workflows.implement.task_tracker_prep"

POPULATED = (
    "# Task Status Tracker\n\n"
    "## Tasks\n\n"
    "### Step 1: Setup\n"
    "- [ ] Implementation\n"
    "- [ ] Quality checks\n\n"
    "## Pull Request\n"
    "- [ ] PR review\n"
)

INVALID = (
    "# Task Status Tracker\n\n"
    "## Tasks\n\n"
    "- [ ] Orphan task\n\n"
    "## Pull Request\n"
    "- [ ] PR review\n"
)


# Reusable LLMResponseDict mock value
def _make_llm_response(text: str = "LLM response text") -> dict[str, Any]:
    return {
        "text": text,
        "session_id": "test-session",
        "version": "1.0",
        "timestamp": "2025-01-01T00:00:00",
        "provider": "claude",
        "raw_response": {},
    }


def _write_tracker(project_dir: Path, content: str) -> Path:
    """Create pr_info/steps/ and write TASK_TRACKER.md."""
    (project_dir / "pr_info" / "steps").mkdir(parents=True, exist_ok=True)
    tracker = project_dir / "pr_info" / "TASK_TRACKER.md"
    tracker.write_text(content, encoding="utf-8")
    return tracker


@dataclass
class PrepMocks:
    """Patched collaborators of prepare_task_tracker."""

    prompt_llm: MagicMock
    store_session: MagicMock
    get_full_status: MagicMock
    commit: MagicMock


@pytest.fixture
def mocks(tmp_path: Path) -> Iterator[PrepMocks]:
    """Patch LLM, git and session collaborators; the LLM writes POPULATED."""

    def populate(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        (tmp_path / "pr_info" / "TASK_TRACKER.md").write_text(
            POPULATED, encoding="utf-8"
        )
        return _make_llm_response("LLM updated the task tracker")

    with (
        patch(f"{PREP}.prepare_llm_environment", return_value={}),
        patch(f"{PREP}.get_prompt", return_value="Task tracker update prompt"),
        patch(f"{PREP}.get_branch_name_for_logging", return_value="branch"),
        patch(f"{PREP}.prompt_llm", side_effect=populate) as prompt_llm,
        patch(f"{PREP}.store_session") as store_session,
        patch(
            f"{PREP}.get_full_status",
            return_value={
                "staged": [],
                "modified": ["pr_info/TASK_TRACKER.md"],
                "untracked": [],
            },
        ) as get_full_status,
        patch(
            f"{PREP}.commit_paths",
            return_value={"success": True, "commit_hash": "abc123"},
        ) as commit,
    ):
        yield PrepMocks(prompt_llm, store_session, get_full_status, commit)


class TestPrepareTaskTrackerDecision:
    """Classifier-based decision before any LLM call."""

    def test_no_steps_dir(self, tmp_path: Path, mocks: PrepMocks) -> None:
        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(tmp_path, "claude")

        assert exc_info.value.reason == "task_tracker_prep_failed"
        assert exc_info.value.stage == "Task tracker preparation"
        mocks.prompt_llm.assert_not_called()

    def test_missing_tracker(self, tmp_path: Path, mocks: PrepMocks) -> None:
        (tmp_path / "pr_info" / "steps").mkdir(parents=True)

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(tmp_path, "claude")

        assert exc_info.value.reason == "task_tracker_prep_failed"
        mocks.prompt_llm.assert_not_called()

    def test_populated_skips_llm_and_commit(
        self, tmp_path: Path, mocks: PrepMocks
    ) -> None:
        _write_tracker(tmp_path, POPULATED)

        assert prepare_task_tracker(tmp_path, "claude") is None  # type: ignore[func-returns-value]

        mocks.prompt_llm.assert_not_called()
        mocks.commit.assert_not_called()

    def test_invalid_without_step_files_fails_without_llm(
        self, tmp_path: Path, mocks: PrepMocks
    ) -> None:
        """No pr_info/steps/step_*.md files, so the reset path is unavailable."""
        tracker = _write_tracker(tmp_path, INVALID)

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(tmp_path, "claude")

        exc = exc_info.value
        assert exc.reason == "general"
        assert exc.stage == "Task tracker validation"
        assert "pr_info/TASK_TRACKER.md line 5:" in str(exc)
        mocks.prompt_llm.assert_not_called()
        mocks.commit.assert_not_called()
        assert tracker.read_text(encoding="utf-8") == INVALID


class TestPrepareTaskTrackerPopulation:
    """EMPTY tracker: one LLM call, then post-check and commit."""

    def test_success(self, tmp_path: Path, mocks: PrepMocks) -> None:
        _write_tracker(tmp_path, TASK_TRACKER_TEMPLATE)

        assert prepare_task_tracker(tmp_path, "claude") is None  # type: ignore[func-returns-value]

        mocks.prompt_llm.assert_called_once()
        call_kwargs = mocks.prompt_llm.call_args[1]
        assert call_kwargs.get("project_dir") == str(tmp_path)
        mocks.get_full_status.assert_called_once_with(tmp_path)
        mocks.commit.assert_called_once()
        _message, paths, project_dir = mocks.commit.call_args[0]
        assert paths == [tmp_path / "pr_info" / "TASK_TRACKER.md"]
        assert project_dir == tmp_path
        mocks.store_session.assert_called_once()
        store_call_kwargs = mocks.store_session.call_args[1]
        assert store_call_kwargs.get("step_name") == "task_tracker"
        assert "implement_sessions" in store_call_kwargs.get("store_path", "")

    @pytest.mark.parametrize("result", [TASK_TRACKER_TEMPLATE, INVALID])
    def test_llm_leaves_tracker_not_populated(
        self, tmp_path: Path, mocks: PrepMocks, result: str
    ) -> None:
        tracker = _write_tracker(tmp_path, TASK_TRACKER_TEMPLATE)

        def write_result(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            tracker.write_text(result, encoding="utf-8")
            return _make_llm_response()

        mocks.prompt_llm.side_effect = write_result

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(tmp_path, "claude")

        assert exc_info.value.reason == "task_tracker_prep_failed"
        mocks.commit.assert_not_called()

    def test_unexpected_files_changed(self, tmp_path: Path, mocks: PrepMocks) -> None:
        _write_tracker(tmp_path, TASK_TRACKER_TEMPLATE)
        mocks.get_full_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md", "src/unexpected_file.py"],
            "untracked": [],
        }

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(tmp_path, "claude")

        assert exc_info.value.reason == "task_tracker_prep_failed"
        assert "src/unexpected_file.py" in str(exc_info.value)
        mocks.commit.assert_not_called()

    def test_ignores_uv_lock(self, tmp_path: Path, mocks: PrepMocks) -> None:
        """uv.lock is in DEFAULT_IGNORED_BUILD_ARTIFACTS and does not block."""
        _write_tracker(tmp_path, TASK_TRACKER_TEMPLATE)
        mocks.get_full_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": ["uv.lock"],
        }

        prepare_task_tracker(tmp_path, "claude")

        mocks.commit.assert_called_once()

    def test_commit_fails(self, tmp_path: Path, mocks: PrepMocks) -> None:
        _write_tracker(tmp_path, TASK_TRACKER_TEMPLATE)
        mocks.commit.return_value = {"success": False, "error": "Commit failed"}

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(tmp_path, "claude")

        assert exc_info.value.reason == "task_tracker_prep_failed"
        assert "Commit failed" in str(exc_info.value)

    def test_exception_is_wrapped(self, tmp_path: Path, mocks: PrepMocks) -> None:
        _write_tracker(tmp_path, TASK_TRACKER_TEMPLATE)
        mocks.prompt_llm.side_effect = RuntimeError("LLM exploded")

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(tmp_path, "claude")

        assert exc_info.value.reason == "task_tracker_prep_failed"
        assert "Error preparing task tracker: RuntimeError: LLM exploded" in str(
            exc_info.value
        )
        assert isinstance(exc_info.value.__cause__, RuntimeError)

    def test_store_session_failure_is_non_critical(
        self, tmp_path: Path, mocks: PrepMocks
    ) -> None:
        _write_tracker(tmp_path, TASK_TRACKER_TEMPLATE)
        mocks.store_session.side_effect = Exception("Storage failure")

        prepare_task_tracker(tmp_path, "claude")

        mocks.commit.assert_called_once()


class TestLogProgressSummary:
    """Test log_progress_summary function."""

    @patch(f"{PREP}.get_step_progress")
    def test_log_progress_summary_no_progress(
        self, mock_get_progress: MagicMock
    ) -> None:
        """Test log_progress_summary when no progress information available."""
        mock_get_progress.return_value = None

        # Should not raise an exception
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )

    @patch(f"{PREP}.get_step_progress")
    def test_log_progress_summary_exception(self, mock_get_progress: MagicMock) -> None:
        """Test log_progress_summary handles exceptions gracefully."""
        mock_get_progress.side_effect = Exception("Progress error")

        # Should not raise an exception
        log_progress_summary(Path("/test/project"))

        mock_get_progress.assert_called_once_with(
            str(Path("/test/project") / "pr_info")
        )

    @patch(f"{PREP}.get_step_progress")
    def test_log_progress_summary_empty_warns(
        self, mock_get_progress: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Empty progress is logged at WARNING level."""
        mock_get_progress.return_value = {}

        with caplog.at_level("WARNING"):
            log_progress_summary(Path("/test/project"))

        assert any(
            r.levelname == "WARNING"
            and "No step progress information available" in r.getMessage()
            for r in caplog.records
        )

    @patch(f"{PREP}.get_step_progress")
    def test_log_progress_summary_exception_warns(
        self, mock_get_progress: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A progress failure is logged at WARNING level."""
        mock_get_progress.side_effect = Exception("Progress error")

        with caplog.at_level("WARNING"):
            log_progress_summary(Path("/test/project"))

        assert any(
            r.levelname == "WARNING"
            and "Could not generate progress summary" in r.getMessage()
            for r in caplog.records
        )
