from pathlib import Path
from typing import Any

import pytest

from mcp_coder.mcp_workspace_github import CommentData
from mcp_coder.workflows.vscodeclaude.workspace import (
    _find_marked_comment,
    create_status_file,
)


def _comment(body: str) -> CommentData:
    return CommentData(
        id=1, body=body, user=None, created_at=None, updated_at=None, url=""
    )


class TestFindMarkedComment:
    """Tests for the _find_marked_comment scan helper."""

    def test_most_recent_marked_returns_its_body(self) -> None:
        """A marked most-recent comment within the window wins."""
        comments = [
            _comment("first"),
            _comment("second"),
            _comment("## ❌ Implementation Failed\ndetails"),
        ]
        assert _find_marked_comment(comments) == "## ❌ Implementation Failed\ndetails"

    def test_scans_backwards_past_unmarked_comment(self) -> None:
        """An unmarked human reply after the marked comment is skipped."""
        comments = [
            _comment("## ❌ Implementation Failed\ndetails"),
            _comment("human reply"),
        ]
        assert _find_marked_comment(comments) == "## ❌ Implementation Failed\ndetails"

    def test_none_marked_returns_none(self) -> None:
        """No marker in the window yields None."""
        comments = [_comment("first"), _comment("second"), _comment("third")]
        assert _find_marked_comment(comments) is None

    def test_fewer_than_window_comments_no_index_error(self) -> None:
        """A single comment is scanned without an index error."""
        comments = [_comment("## ❌ Implementation Failed\ndetails")]
        assert _find_marked_comment(comments) == "## ❌ Implementation Failed\ndetails"

    def test_marker_on_second_line_not_matched(self) -> None:
        """A marker outside the first line of the body is not matched."""
        comments = [_comment("Implementation Failed\n❌ details")]
        assert _find_marked_comment(comments) is None

    def test_empty_body_in_window_no_crash(self) -> None:
        """An empty body is treated as unmarked, not a crash."""
        comments = [_comment(""), _comment("second")]
        assert _find_marked_comment(comments) is None


class TestCreateStatusFileNote:
    """Tests for the _fetch_marked_comment wiring into create_status_file."""

    def _create(self, tmp_path: Path) -> str:
        create_status_file(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Add feature",
            status="status-07:code-review",
            repo_full_name="owner/repo",
            branch_name="feature-123",
            issue_url="https://github.com/owner/repo/issues/123",
            is_intervention=False,
        )
        return (tmp_path / ".vscodeclaude_status.txt").read_text(encoding="utf-8")

    def test_marked_comment_found_appends_note(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """A ❌-marked comment among the last 3 gets appended to the status file."""
        marked_body = "## ❌ Implementation Failed\nSome detail text."
        comments = [
            _comment("first"),
            _comment("second"),
            _comment(marked_body),
        ]

        class FakeIssueManager:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            def get_comments(self, issue_number: int) -> list[CommentData]:
                return comments

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.IssueManager",
            FakeIssueManager,
        )

        content = self._create(tmp_path)

        assert "❌ Last automated note:" in content
        assert marked_body in content

    def test_no_marked_comment_leaves_status_file_unchanged(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """No marker in the last 3 comments means no new block is appended."""
        comments = [_comment("first"), _comment("second"), _comment("third")]

        class FakeIssueManager:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            def get_comments(self, issue_number: int) -> list[CommentData]:
                return comments

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.IssueManager",
            FakeIssueManager,
        )

        content = self._create(tmp_path)

        assert "❌ Last automated note:" not in content

    def test_fetch_failure_leaves_status_file_unchanged_and_logs_warning(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A raising fetch is swallowed; no block appended, warning logged."""

        class FailingIssueManager:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise RuntimeError("boom")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.IssueManager",
            FailingIssueManager,
        )

        with caplog.at_level("WARNING"):
            content = self._create(tmp_path)

        assert "❌ Last automated note:" not in content
        assert "123" in caplog.text

    def test_fewer_than_three_comments_still_finds_marked(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """A single marked comment is found even below the 3-comment window."""
        marked_body = "## ❌ Implementation Failed\nonly comment"
        comments = [_comment(marked_body)]

        class FakeIssueManager:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            def get_comments(self, issue_number: int) -> list[CommentData]:
                return comments

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.IssueManager",
            FakeIssueManager,
        )

        content = self._create(tmp_path)

        assert "❌ Last automated note:" in content
        assert marked_body in content
