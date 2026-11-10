"""Tests for rescue_commit in check_loop."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.workflow_steps.commit import FormatterConfigError
from mcp_coder.workflow_steps.constants import BLOCKED_FILE, COMMIT_MESSAGE_FILE
from mcp_coder.workflows.implement.check_loop import rescue_commit

_CL = "mcp_coder.workflows.implement.check_loop"


@dataclass
class _Mocks:
    """Patched collaborators of rescue_commit."""

    formatters: MagicMock
    commit: MagicMock
    push: MagicMock


@pytest.fixture(name="mocks")
def _mocks_fixture() -> Iterator[_Mocks]:
    """Formatting, commit and push all succeed."""
    with (
        patch(f"{_CL}.run_formatters", return_value=True) as formatters,
        patch(
            f"{_CL}.commit_all_changes",
            return_value={"success": True, "commit_hash": "abc1234", "error": None},
        ) as commit,
        patch(f"{_CL}.push_changes", return_value=True) as push,
    ):
        yield _Mocks(formatters, commit, push)


class TestRescueCommit:
    """rescue_commit formats, commits with a fixed message and pushes."""

    def test_commit_message(self, mocks: _Mocks, tmp_path: Path) -> None:
        """The commit message carries the failure reason."""
        rescue_commit(tmp_path, "general")

        mocks.commit.assert_called_once_with(
            "wip(implement): checks failed (general)", tmp_path
        )

    def test_clears_marker_and_message_file_before_commit(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """Neither the blocked marker nor a stale commit message is committed."""
        (tmp_path / "pr_info").mkdir()
        (tmp_path / BLOCKED_FILE).write_text("stuck", encoding="utf-8")
        (tmp_path / COMMIT_MESSAGE_FILE).write_text("old msg", encoding="utf-8")
        seen: list[bool] = []

        def _commit(*_args: Any) -> dict[str, Any]:
            seen.append((tmp_path / BLOCKED_FILE).exists())
            seen.append((tmp_path / COMMIT_MESSAGE_FILE).exists())
            return {"success": True, "commit_hash": "abc1234", "error": None}

        mocks.commit.side_effect = _commit

        rescue_commit(tmp_path, "blocked")

        assert seen == [False, False]

    def test_formatter_failure_still_commits(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """A failed formatter run is logged, not fatal."""
        mocks.formatters.return_value = False

        assert rescue_commit(tmp_path, "general") == "pushed abc1234"
        mocks.commit.assert_called_once()

    def test_formatter_config_error_still_commits(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """A formatter config error is logged, not fatal."""
        mocks.formatters.side_effect = FormatterConfigError("bad config")

        assert rescue_commit(tmp_path, "general") == "pushed abc1234"
        mocks.commit.assert_called_once()

    def test_pushed(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A successful push reports the sha."""
        assert rescue_commit(tmp_path, "timeout") == "pushed abc1234"
        mocks.push.assert_called_once_with(tmp_path)

    def test_push_failed(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A failed push keeps the local commit."""
        mocks.push.return_value = False

        assert rescue_commit(tmp_path, "timeout") == "committed abc1234, push failed"

    def test_nothing_to_commit(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A clean tree is reported and nothing is pushed."""
        mocks.commit.return_value = {
            "success": True,
            "commit_hash": None,
            "error": None,
        }

        assert rescue_commit(tmp_path, "general") == "nothing to commit"
        mocks.push.assert_not_called()

    def test_commit_failed(self, mocks: _Mocks, tmp_path: Path) -> None:
        """A failed commit reports the error and pushes nothing."""
        mocks.commit.return_value = {
            "success": False,
            "commit_hash": None,
            "error": "index locked",
        }

        assert rescue_commit(tmp_path, "general") == "commit failed: index locked"
        mocks.push.assert_not_called()

    @pytest.mark.parametrize(
        "target,exc",
        [
            ("commit", RuntimeError("git broke")),
            ("commit", LLMTimeoutError("slow")),
            ("push", RuntimeError("net down")),
            ("push", LLMTimeoutError("slow")),
        ],
    )
    def test_never_raises(
        self, mocks: _Mocks, tmp_path: Path, target: str, exc: Exception
    ) -> None:
        """Any exception becomes a 'commit failed' line."""
        getattr(mocks, target).side_effect = exc

        result = rescue_commit(tmp_path, "general")

        assert result.startswith("commit failed: ")
