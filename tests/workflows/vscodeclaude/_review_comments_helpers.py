"""Shared constants and builders for the review-comment check tests."""

from typing import Any

import pytest

from mcp_coder.mcp_workspace_github import (
    ChangesRequestedData,
    ConversationCommentData,
    EventData,
    IssueData,
    PullRequestData,
    ReviewThreadData,
)
from mcp_coder.utils.log_utils import OUTPUT
from tests.github_factories import make_issue_data

CHECKS = "mcp_coder.workflows.vscodeclaude.checks"
REVIEW_LABEL = "status-91:pr-review-comments"
CREATED_LABEL = "status-10:pr-created"

BEFORE_WATERMARK = "2024-01-15T00:00:00+00:00"
AFTER_WATERMARK = "2024-07-01T00:00:00+00:00"


def _make_pr(
    user: str | None = "owner", association: str | None = "OWNER"
) -> PullRequestData:
    return {
        "number": 1,
        "title": "PR",
        "body": "",
        "state": "open",
        "head_branch": "1-fix",
        "head_sha": None,
        "base_branch": "main",
        "url": "https://github.com/owner/repo/pull/1",
        "created_at": None,
        "updated_at": None,
        "user": user,
        "mergeable": None,
        "mergeable_state": "clean",
        "merged": False,
        "draft": False,
        "assignees": [],
        "author_association": association,
    }


PR = _make_pr()


def _labeled(label: str, created_at: str) -> EventData:
    return {
        "event": "labeled",
        "label": label,
        "created_at": created_at,
        "actor": "someone",
    }


def _thread(
    author: str = "reviewer", association: str | None = "MEMBER"
) -> ReviewThreadData:
    return {
        "path": "src/x.py",
        "line": 1,
        "author": author,
        "body": "fix this",
        "diff_hunk": "@@ -1 +1 @@",
        "comment_id": 1,
        "thread_id": "T_1",
        "author_association": association,
    }


def _review(
    submitted_at: str | None,
    body: str = "please fix",
    *,
    author: str = "reviewer",
    association: str | None = "MEMBER",
) -> ChangesRequestedData:
    return {
        "author": author,
        "body": body,
        "submitted_at": submitted_at,
        "author_association": association,
    }


def _comment(
    created_at: str | None,
    body: str = "y",
    comment_id: int = 1,
    *,
    author: str = "reviewer",
    association: str | None = "MEMBER",
) -> ConversationCommentData:
    return {
        "author": author,
        "body": body,
        "id": comment_id,
        "created_at": created_at,
        "author_association": association,
    }


def _output_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == OUTPUT]


# Watermark = 2024-06-01 (status-10 relabel after the last status-91).
WATERMARK_EVENTS: list[EventData] = [
    _labeled(CREATED_LABEL, "2024-01-01T00:00:00+00:00"),
    _labeled(REVIEW_LABEL, "2024-03-01T00:00:00+00:00"),
    _labeled(CREATED_LABEL, "2024-06-01T00:00:00+00:00"),
]


def _empty_pr_feedback(**overrides: Any) -> dict[str, Any]:
    feedback: dict[str, Any] = {
        "unresolved_threads": [],
        "resolved_thread_count": 0,
        "changes_requested": [],
        "conversation_comments": [],
        "alerts": [],
        "unavailable": {},
    }
    feedback.update(overrides)
    return feedback


def _make_issue(number: int) -> IssueData:
    return make_issue_data(
        number=number,
        title="PR Created Issue",
        labels=["status-10:pr-created"],
        assignees=["testuser"],
    )


MOCK_REVIEW_LABELS_CONFIG: dict[str, Any] = {
    "workflow_labels": [
        {
            "internal_id": "pr_created",
            "name": "status-10:pr-created",
            "color": "8b5cf6",
            "description": "Pull request created, awaiting approval/merge",
            "category": "human_action",
        },
        {
            "internal_id": "pr_review_comments",
            "name": "status-91:pr-review-comments",
            "color": "b60205",
            "description": (
                "PR has new review comments, unresolved threads, or a "
                "changes-requested review"
            ),
            "category": "human_action",
        },
    ],
    "ignore_labels": [],
}
