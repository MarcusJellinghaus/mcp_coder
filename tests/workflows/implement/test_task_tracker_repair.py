"""Tests for task tracker LLM rounds, guard, byte restore and INVALID repair."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.workflow_utils.task_tracker import TASK_TRACKER_TEMPLATE
from mcp_coder.workflows.implement.task_tracker_prep import (
    TrackerPrepError,
    prepare_task_tracker,
)

PREP = "mcp_coder.workflows.implement.task_tracker_prep"

POPULATED = (
    "# Task Status Tracker\n\n"
    "## Tasks\n\n"
    "### Step 1: Setup\n"
    "- [ ] Implementation\n\n"
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

# CRLF proves the restore is byte-exact, not a text round-trip
EMPTY_CRLF = TASK_TRACKER_TEMPLATE.replace("\n", "\r\n").encode("utf-8")

TRACKER_ONLY = {"staged": [], "modified": ["pr_info/TASK_TRACKER.md"], "untracked": []}


# Title plus "## Instructions for LLM" block of the template; contains an [x] line.
INSTRUCTIONS = TASK_TRACKER_TEMPLATE.split("## Tasks")[0]

# Issue #1146: flat checkboxes under "## Tasks", nothing checked
FLAT_1146 = TASK_TRACKER_TEMPLATE.replace(
    "<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->",
    "- [ ] Do the thing\n- [ ] Do another thing",
)

# "## Step N" headers inside "## Tasks", one task checked
STEP_TRACKER = (
    INSTRUCTIONS + "## Tasks\n\n"
    "## Step 1: Setup\n"
    "- [x] Implementation\n"
    "- [ ] Commit message prepared\n\n"
    "## Step 2: More\n"
    "- [ ] Implementation\n"
    "- [ ] Commit message prepared\n\n"
    "## Pull Request\n"
    "- [ ] PR review\n"
)

RESTRUCTURED = STEP_TRACKER.replace("## Step ", "### Step ")


def _prompts(_path: str, name: str) -> str:
    if name == "Task Tracker Feedback Prompt":
        return "FEEDBACK\n[violations]\n[expected_format]"
    if name == "Task Tracker Restructure Prompt":
        return "RESTRUCTURE\n[violations]\n[expected_format]"
    return "UPDATE PROMPT"


@dataclass
class RoundMocks:
    """Patched collaborators plus the tracker path."""

    tracker: Path
    prompt_llm: MagicMock
    get_full_status: MagicMock
    commit: MagicMock

    def llm_writes(self, *contents: str) -> None:
        """Make successive LLM calls write ``contents`` (last one repeats)."""
        calls = iter(contents)
        last = [contents[-1]]

        def write(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            last[0] = next(calls, last[0])
            self.tracker.write_text(last[0], encoding="utf-8")
            return _response()

        self.prompt_llm.side_effect = write


def _response() -> dict[str, Any]:
    return {
        "text": "done",
        "session_id": "session-1",
        "version": "1.0",
        "timestamp": "2025-01-01T00:00:00",
        "provider": "claude",
        "raw_response": {},
    }


@pytest.fixture
def mocks(tmp_path: Path) -> Iterator[RoundMocks]:
    """EMPTY CRLF tracker with patched LLM, git and session collaborators."""
    (tmp_path / "pr_info" / "steps").mkdir(parents=True)
    tracker = tmp_path / "pr_info" / "TASK_TRACKER.md"
    tracker.write_bytes(EMPTY_CRLF)
    with (
        patch(f"{PREP}.prepare_llm_environment", return_value={}),
        patch(f"{PREP}.get_prompt", side_effect=_prompts),
        patch(f"{PREP}.get_branch_name_for_logging", return_value="branch"),
        patch(f"{PREP}.prompt_llm") as prompt_llm,
        patch(f"{PREP}.store_session"),
        patch(f"{PREP}.get_full_status", return_value=TRACKER_ONLY) as status,
        patch(
            f"{PREP}.commit_paths",
            return_value={"success": True, "commit_hash": "abc123"},
        ) as commit,
    ):
        yield RoundMocks(tracker, prompt_llm, status, commit)


def _prompt_text(call: Any) -> str:
    return str(call.args[0])


class TestFeedbackRounds:
    """Population with up to 3 feedback rounds in one session."""

    def test_populates_and_commits_only_tracker(self, mocks: RoundMocks) -> None:
        mocks.llm_writes(POPULATED)

        prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert mocks.prompt_llm.call_count == 1
        assert mocks.prompt_llm.call_args.kwargs["session_id"] is None
        mocks.commit.assert_called_once()
        assert mocks.commit.call_args.args[1] == [mocks.tracker]

    @pytest.mark.parametrize("result", [TASK_TRACKER_TEMPLATE, INVALID])
    def test_fails_after_four_calls_and_restores(
        self, mocks: RoundMocks, result: str
    ) -> None:
        mocks.llm_writes(result)

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert exc_info.value.reason == "task_tracker_prep_failed"
        assert "after 4 LLM calls" in str(exc_info.value)
        calls = mocks.prompt_llm.call_args_list
        assert len(calls) == 4
        assert calls[0].kwargs["session_id"] is None
        assert _prompt_text(calls[0]) == "UPDATE PROMPT"
        for call in calls[1:]:
            assert call.kwargs["session_id"] == "session-1"
            text = _prompt_text(call)
            assert text.startswith("FEEDBACK")
            assert "[violations]" not in text
            assert "[expected_format]" not in text
            assert "### Step 1: <title>" in text
        mocks.commit.assert_not_called()
        assert mocks.tracker.read_bytes() == EMPTY_CRLF

    def test_fixed_on_second_call(self, mocks: RoundMocks) -> None:
        mocks.llm_writes(INVALID, POPULATED)

        prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert mocks.prompt_llm.call_count == 2
        assert "line 5:" in _prompt_text(mocks.prompt_llm.call_args_list[1])
        mocks.commit.assert_called_once()

    def test_no_change_counts_as_failed_round(self, mocks: RoundMocks) -> None:
        mocks.prompt_llm.return_value = _response()
        mocks.get_full_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": [],
        }

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert "after 4 LLM calls" in str(exc_info.value)
        assert "no '### Step N:' sections were added" in str(exc_info.value)
        assert mocks.prompt_llm.call_count == 4


class TestGuardAndRestore:
    """Changed-files guard and byte-exact restore on any failure."""

    def test_other_file_changed_stops_immediately(self, mocks: RoundMocks) -> None:
        mocks.llm_writes(POPULATED)
        mocks.get_full_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md", "src/x.py"],
            "untracked": [],
        }

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert "src/x.py" in str(exc_info.value)
        assert mocks.prompt_llm.call_count == 1
        mocks.commit.assert_not_called()
        assert mocks.tracker.read_bytes() == EMPTY_CRLF

    def test_llm_timeout_not_retried(self, mocks: RoundMocks) -> None:
        mocks.prompt_llm.side_effect = LLMTimeoutError("silent for 600s")

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert exc_info.value.reason == "task_tracker_prep_failed"
        assert "LLMTimeoutError" in str(exc_info.value)
        assert mocks.prompt_llm.call_count == 1
        assert mocks.tracker.read_bytes() == EMPTY_CRLF

    def test_system_exit_propagates_and_restores(self, mocks: RoundMocks) -> None:
        def modify_then_exit(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            mocks.tracker.write_text(INVALID, encoding="utf-8")
            raise SystemExit(1)

        mocks.prompt_llm.side_effect = modify_then_exit

        with pytest.raises(SystemExit):
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert mocks.tracker.read_bytes() == EMPTY_CRLF

    @pytest.mark.parametrize(
        "fail_commit",
        [
            lambda m: setattr(
                m.commit, "return_value", {"success": False, "error": "boom"}
            ),
            lambda m: setattr(m.commit, "side_effect", RuntimeError("boom")),
        ],
    )
    def test_commit_failure_restores(
        self, mocks: RoundMocks, fail_commit: Callable[[RoundMocks], None]
    ) -> None:
        mocks.llm_writes(POPULATED)
        fail_commit(mocks)

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert "boom" in str(exc_info.value)
        assert mocks.tracker.read_bytes() == EMPTY_CRLF


def _set_original(mocks: RoundMocks, content: str) -> bytes:
    """Write ``content`` as the original tracker and return its bytes."""
    original = content.encode("utf-8")
    mocks.tracker.write_bytes(original)
    return original


class TestResetRepair:
    """INVALID tracker without [x]: reset to the template, then populate."""

    def test_resets_before_llm_and_populates(self, mocks: RoundMocks) -> None:
        _set_original(mocks, FLAT_1146)
        (mocks.tracker.parent / "steps" / "step_1.md").write_text("# Step 1")
        seen: list[str] = []

        def populate(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            seen.append(mocks.tracker.read_text(encoding="utf-8"))
            mocks.tracker.write_text(POPULATED, encoding="utf-8")
            return _response()

        mocks.prompt_llm.side_effect = populate

        prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert seen == [TASK_TRACKER_TEMPLATE]
        assert _prompt_text(mocks.prompt_llm.call_args_list[0]) == "UPDATE PROMPT"
        mocks.commit.assert_called_once()
        assert mocks.tracker.read_text(encoding="utf-8") == POPULATED

    def test_no_step_files_fails_without_llm(self, mocks: RoundMocks) -> None:
        original = _set_original(mocks, FLAT_1146)
        (mocks.tracker.parent / "steps" / "summary.md").write_text("# Summary")

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert exc_info.value.reason == "general"
        assert "step_*.md" in str(exc_info.value)
        mocks.prompt_llm.assert_not_called()
        mocks.commit.assert_not_called()
        assert mocks.tracker.read_bytes() == original

    def test_population_still_invalid_restores(self, mocks: RoundMocks) -> None:
        original = _set_original(mocks, FLAT_1146)
        (mocks.tracker.parent / "steps" / "step_1.md").write_text("# Step 1")
        mocks.llm_writes(INVALID)

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert exc_info.value.reason == "general"
        assert exc_info.value.stage == "Task tracker validation"
        assert mocks.prompt_llm.call_count == 4
        mocks.commit.assert_not_called()
        assert mocks.tracker.read_bytes() == original


class TestRestructureRepair:
    """INVALID tracker with [x]: LLM restructure checked against the original."""

    def test_restructure_success(self, mocks: RoundMocks) -> None:
        _set_original(mocks, STEP_TRACKER)
        seen: list[str] = []

        def restructure(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            seen.append(mocks.tracker.read_text(encoding="utf-8"))
            mocks.tracker.write_text(RESTRUCTURED, encoding="utf-8")
            return _response()

        mocks.prompt_llm.side_effect = restructure

        prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert seen == [STEP_TRACKER]
        first = _prompt_text(mocks.prompt_llm.call_args_list[0])
        assert first.startswith("RESTRUCTURE")
        assert "[violations]" not in first
        assert "[expected_format]" not in first
        assert "pr_info/TASK_TRACKER.md line 24" in first
        assert mocks.prompt_llm.call_count == 1
        mocks.commit.assert_called_once()
        assert "- [x] Implementation" in mocks.tracker.read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        "bad",
        [
            RESTRUCTURED.replace("- [x] Implementation", "- [ ] Implementation"),
            RESTRUCTURED.replace("- [x] Implementation\n", ""),
            RESTRUCTURED.replace("- [x] Implementation", "- [x] Implemented it"),
            RESTRUCTURED.replace(
                "- [x] Implementation\n", "- [x] Implementation\n- [ ] Extra task\n"
            ),
        ],
        ids=["toggled", "deleted", "reworded", "added_under_checked_step"],
    )
    def test_bad_restructure_fails_after_three_attempts(
        self, mocks: RoundMocks, bad: str
    ) -> None:
        original = _set_original(mocks, STEP_TRACKER)
        mocks.llm_writes(bad)

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        exc = exc_info.value
        assert exc.reason == "general"
        assert "after 3 LLM calls" in str(exc)
        assert "Original violations:" in str(exc)
        assert "pr_info/TASK_TRACKER.md line 24" in str(exc)
        calls = mocks.prompt_llm.call_args_list
        assert len(calls) == 3
        assert calls[0].kwargs["session_id"] is None
        assert all(c.kwargs["session_id"] == "session-1" for c in calls[1:])
        mocks.commit.assert_not_called()
        assert mocks.tracker.read_bytes() == original

    def test_unchanged_tracker_is_failed_attempt(self, mocks: RoundMocks) -> None:
        original = _set_original(mocks, STEP_TRACKER)
        mocks.prompt_llm.return_value = _response()

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert "after 3 LLM calls" in str(exc_info.value)
        assert mocks.prompt_llm.call_count == 3
        assert mocks.tracker.read_bytes() == original

    def test_guard_trip_fails_immediately(self, mocks: RoundMocks) -> None:
        original = _set_original(mocks, STEP_TRACKER)
        mocks.llm_writes(RESTRUCTURED)
        mocks.get_full_status.return_value = {
            "staged": [],
            "modified": ["pr_info/TASK_TRACKER.md"],
            "untracked": ["notes.md"],
        }

        with pytest.raises(TrackerPrepError) as exc_info:
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert exc_info.value.reason == "general"
        assert "notes.md" in str(exc_info.value)
        assert mocks.prompt_llm.call_count == 1
        mocks.commit.assert_not_called()
        assert mocks.tracker.read_bytes() == original

    def test_system_exit_restores(self, mocks: RoundMocks) -> None:
        original = _set_original(mocks, STEP_TRACKER)

        def modify_then_exit(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            mocks.tracker.write_text(RESTRUCTURED, encoding="utf-8")
            raise SystemExit(1)

        mocks.prompt_llm.side_effect = modify_then_exit

        with pytest.raises(SystemExit):
            prepare_task_tracker(mocks.tracker.parents[1], "claude")

        assert mocks.tracker.read_bytes() == original
