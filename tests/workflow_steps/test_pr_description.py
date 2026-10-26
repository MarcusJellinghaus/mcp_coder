"""Tests for mcp_coder.workflow_steps.pr_description."""

import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.workflow_steps.pr_description import (
    closing_issue_numbers,
    refresh_pr_description,
)

_MODULE = "mcp_coder.workflow_steps.pr_description"


class TestClosingIssueNumbers:
    """Test closing_issue_numbers function."""

    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ("Closes #3\nfixes #1, resolves: #3", [1, 3]),
            ("No reference", []),
            ("", []),
            ("#5", []),
        ],
    )
    def test_closing_issue_numbers(self, body: str, expected: list[int]) -> None:
        """Returns sorted, de-duplicated numbers of closed issues."""
        assert closing_issue_numbers(body) == expected


_LLM_TEXT = "TITLE: feat(x): new title\nBODY:\n## Summary\nNew body"


@pytest.fixture(name="mocks")
def _mocks() -> Iterator[dict[str, MagicMock]]:
    """Patch every collaborator of refresh_pr_description."""
    with (
        patch(f"{_MODULE}.PullRequestManager") as mgr_cls,
        patch(f"{_MODULE}.detect_base_branch", return_value="main") as base,
        patch(f"{_MODULE}.get_branch_diff", return_value="diff --git a b") as diff,
        patch(f"{_MODULE}.prompt_llm", return_value={"text": _LLM_TEXT}) as llm,
        patch(f"{_MODULE}.prepare_llm_environment", return_value={}),
        patch(f"{_MODULE}.get_branch_name_for_logging", return_value="b"),
    ):
        mgr = mgr_cls.return_value
        mgr.find_pull_request_by_head.return_value = [{"number": 7}]
        mgr.get_pull_request.return_value = {
            "number": 7,
            "title": "old title",
            "body": "Old body\n\nCloses #12",
        }
        mgr.update_pull_request.return_value = {"number": 7}
        yield {"mgr": mgr, "base": base, "diff": diff, "llm": llm}


def _refresh() -> bool:
    return refresh_pr_description(Path("/repo"), "feature", "claude")


class TestRefreshPrDescription:
    """Test refresh_pr_description function."""

    def test_updates_with_parsed_title_and_kept_closing_ref(
        self, mocks: dict[str, MagicMock]
    ) -> None:
        """LLM TITLE/BODY -> PR updated, current closing reference kept."""
        assert _refresh() is True

        kwargs = mocks["mgr"].update_pull_request.call_args
        assert kwargs.args == (7,)
        assert kwargs.kwargs["title"] == "feat(x): new title"
        assert "New body" in kwargs.kwargs["body"]
        assert "Closes #12" in kwargs.kwargs["body"]
        prompt = mocks["llm"].call_args.args[0]
        assert "old title" in prompt
        assert "Old body" in prompt
        assert "diff --git a b" in prompt

    def test_keeps_all_closing_refs(self, mocks: dict[str, MagicMock]) -> None:
        """Every issue the current body closes stays closed."""
        mocks["mgr"].get_pull_request.return_value = {
            "number": 7,
            "title": "old",
            "body": "Closes #12\nFixes #13",
        }

        assert _refresh() is True

        body = mocks["mgr"].update_pull_request.call_args.kwargs["body"]
        assert closing_issue_numbers(body) == [12, 13]

    def test_unchanged_skips_update(self, mocks: dict[str, MagicMock]) -> None:
        """LLM answers UNCHANGED -> no update."""
        mocks["llm"].return_value = {"text": "  UNCHANGED\n"}

        assert _refresh() is False

        mocks["mgr"].update_pull_request.assert_not_called()

    def test_no_open_pr(self, mocks: dict[str, MagicMock]) -> None:
        """No open PR for the branch -> False, no LLM call."""
        mocks["mgr"].find_pull_request_by_head.return_value = []

        assert _refresh() is False

        mocks["llm"].assert_not_called()
        mocks["mgr"].update_pull_request.assert_not_called()

    def test_empty_diff(self, mocks: dict[str, MagicMock]) -> None:
        """Empty diff -> False, no LLM call."""
        mocks["diff"].return_value = "  "

        assert _refresh() is False

        mocks["llm"].assert_not_called()

    def test_no_base_branch(self, mocks: dict[str, MagicMock]) -> None:
        """Unknown base branch -> False, no LLM call."""
        mocks["base"].return_value = None

        assert _refresh() is False

        mocks["llm"].assert_not_called()

    def test_llm_error_logs_warning(
        self, mocks: dict[str, MagicMock], caplog: pytest.LogCaptureFixture
    ) -> None:
        """LLM raises -> False with a non-blocking warning."""
        mocks["llm"].side_effect = RuntimeError("boom")

        with caplog.at_level(logging.WARNING, logger=_MODULE):
            assert _refresh() is False

        assert "PR description refresh failed (non-blocking): boom" in caplog.text
        mocks["mgr"].update_pull_request.assert_not_called()

    def test_update_failure_returns_false(self, mocks: dict[str, MagicMock]) -> None:
        """update_pull_request returns {} on GitHub error -> False."""
        mocks["mgr"].update_pull_request.return_value = {}

        assert _refresh() is False


def test_refresh_prompt_has_placeholders() -> None:
    """The refresh prompt loads from prompts.md with all placeholders."""
    prompt = get_prompt(str(PROMPTS_FILE_PATH), "PR Description Refresh")

    for placeholder in ("[pr_title]", "[pr_body]", "[git_diff_content]"):
        assert placeholder in prompt
    assert "UNCHANGED" in prompt
