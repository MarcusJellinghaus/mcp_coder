"""Tests for the data-layer branch info service."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.services.branch_info import (
    BranchInfo,
    get_branch_info,
    get_branch_only,
    get_pr_for_issue,
)

PROJECT_DIR = Path("/fake/project")

BRANCH_INFO_MODULE = "mcp_coder.services.branch_info"


def _fake_repo_id(
    owner: str = "owner",
    name: str = "repo",
    https: str = "https://github.com/owner/repo.git",
) -> Mock:
    """Build a stand-in for ``RepoIdentifier`` with the attributes we touch."""
    repo_id = Mock(spec=["owner", "repo_name", "https_url"])
    repo_id.owner = owner
    repo_id.repo_name = name
    repo_id.https_url = https
    return repo_id


def _issue(
    labels: list[str], title: str = "Some title", number: int = 42
) -> dict[str, Any]:
    return {
        "number": number,
        "state": "open",
        "labels": labels,
        "title": title,
        "body": "",
        "assignees": [],
        "user": "u",
        "created_at": "2026-04-30T08:00:00Z",
        "updated_at": "2026-04-30T09:00:00Z",
        "url": f"https://github.com/owner/repo/issues/{number}",
        "locked": False,
    }


# ---------------------------------------------------------------------------
# get_branch_info
# ---------------------------------------------------------------------------


def test_no_git_repo_returns_empty_branchinfo() -> None:
    with patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=False):
        info = get_branch_info(PROJECT_DIR)

    assert info == BranchInfo(
        is_git_repo=False,
        branch_name=None,
        is_dirty=False,
        issue_number=None,
        issue_title=None,
        issue_status_label=None,
        cache_last_checked=None,
    )


def test_branch_without_issue_number() -> None:
    sentinel = Mock(side_effect=AssertionError("must not be called"))
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(f"{BRANCH_INFO_MODULE}.get_current_branch_name", return_value="main"),
        patch(f"{BRANCH_INFO_MODULE}.is_working_directory_clean", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=None,
        ),
        patch(f"{BRANCH_INFO_MODULE}.get_repository_identifier", side_effect=sentinel),
        patch(f"{BRANCH_INFO_MODULE}.get_all_cached_issues", side_effect=sentinel),
    ):
        info = get_branch_info(PROJECT_DIR)

    assert info.is_git_repo is True
    assert info.branch_name == "main"
    assert info.is_dirty is False
    assert info.issue_number is None
    assert info.issue_title is None
    assert info.issue_status_label is None
    assert info.cache_last_checked is None


def test_branch_with_issue_populates_from_cache() -> None:
    repo_id = _fake_repo_id()
    issue = _issue(["status-04:plan-review", "bug"], title="Add bar", number=42)

    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.get_current_branch_name",
            return_value="42-feature",
        ),
        patch(f"{BRANCH_INFO_MODULE}.is_working_directory_clean", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=42,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.get_repository_identifier",
            return_value=repo_id,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.get_cache_file_path",
            return_value=Path("/fake/cache.json"),
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.load_cache_file",
            return_value={
                "last_checked": "2026-04-30T10:00:00+00:00",
                "issues": {},
            },
        ),
        patch(f"{BRANCH_INFO_MODULE}.IssueManager"),
        patch(
            f"{BRANCH_INFO_MODULE}.get_all_cached_issues",
            return_value=[issue],
        ),
    ):
        info = get_branch_info(PROJECT_DIR)

    assert info.issue_number == 42
    assert info.issue_title == "Add bar"
    assert info.issue_status_label == "status-04:plan-review"
    assert info.cache_last_checked == datetime(2026, 4, 30, 10, 0, tzinfo=timezone.utc)


def test_gh_failure_keeps_branch_fields_returns_none_for_issue() -> None:
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.get_current_branch_name",
            return_value="42-feature",
        ),
        patch(f"{BRANCH_INFO_MODULE}.is_working_directory_clean", return_value=False),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=42,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.get_repository_identifier",
            return_value=_fake_repo_id(),
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.get_cache_file_path",
            return_value=Path("/fake/cache.json"),
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.load_cache_file",
            side_effect=RuntimeError("boom"),
        ),
    ):
        info = get_branch_info(PROJECT_DIR)

    assert info.is_git_repo is True
    assert info.branch_name == "42-feature"
    assert info.is_dirty is True
    assert info.issue_number == 42
    assert info.issue_title is None
    assert info.issue_status_label is None
    assert info.cache_last_checked is None


def test_cache_miss_returns_branchinfo_with_none_issue_fields() -> None:
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.get_current_branch_name",
            return_value="42-feature",
        ),
        patch(f"{BRANCH_INFO_MODULE}.is_working_directory_clean", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=42,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.get_repository_identifier",
            return_value=_fake_repo_id(),
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.get_cache_file_path",
            return_value=Path("/fake/cache.json"),
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.load_cache_file",
            return_value={"last_checked": None, "issues": {}},
        ),
        patch(f"{BRANCH_INFO_MODULE}.IssueManager"),
        patch(f"{BRANCH_INFO_MODULE}.get_all_cached_issues", return_value=[]),
    ):
        info = get_branch_info(PROJECT_DIR)

    assert info.is_git_repo is True
    assert info.branch_name == "42-feature"
    assert info.is_dirty is False
    assert info.issue_number == 42
    assert info.issue_title is None
    assert info.issue_status_label is None
    assert info.cache_last_checked is None


@pytest.mark.parametrize("dirty_flag,expected_is_dirty", [(False, True), (True, False)])
def test_dirty_detection_uses_shim(dirty_flag: bool, expected_is_dirty: bool) -> None:
    sentinel = Mock(side_effect=AssertionError("must not be called"))
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(f"{BRANCH_INFO_MODULE}.get_current_branch_name", return_value="main"),
        patch(
            f"{BRANCH_INFO_MODULE}.is_working_directory_clean",
            return_value=dirty_flag,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=None,
        ),
        patch("subprocess.run", side_effect=sentinel),
    ):
        info = get_branch_info(PROJECT_DIR)

    assert info.is_dirty is expected_is_dirty


def test_no_repo_remote_skips_gh_lookups() -> None:
    sentinel = Mock(side_effect=AssertionError("must not be called"))
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.get_current_branch_name",
            return_value="42-feature",
        ),
        patch(f"{BRANCH_INFO_MODULE}.is_working_directory_clean", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=42,
        ),
        patch(f"{BRANCH_INFO_MODULE}.get_repository_identifier", return_value=None),
        patch(f"{BRANCH_INFO_MODULE}.get_all_cached_issues", side_effect=sentinel),
        patch(f"{BRANCH_INFO_MODULE}.get_cache_file_path", side_effect=sentinel),
        patch(f"{BRANCH_INFO_MODULE}.load_cache_file", side_effect=sentinel),
    ):
        info = get_branch_info(PROJECT_DIR)

    assert info.issue_number == 42
    assert info.issue_title is None
    assert info.issue_status_label is None
    assert info.cache_last_checked is None


@pytest.mark.parametrize(
    "labels,expected_label",
    [
        (["status-04:plan-review"], "status-04:plan-review"),
        (["bug", "status-04:plan-review"], "status-04:plan-review"),
        (
            ["status-04:plan-review", "status-05:approved"],
            "status-04:plan-review",
        ),
        ([], None),
        (["bug"], None),
    ],
)
def test_status_label_picks_first_status_prefix(
    labels: list[str], expected_label: str | None
) -> None:
    repo_id = _fake_repo_id()
    issue = _issue(labels, number=42)
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.get_current_branch_name",
            return_value="42-feature",
        ),
        patch(f"{BRANCH_INFO_MODULE}.is_working_directory_clean", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=42,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.get_repository_identifier",
            return_value=repo_id,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.get_cache_file_path",
            return_value=Path("/fake/cache.json"),
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.load_cache_file",
            return_value={"last_checked": None, "issues": {}},
        ),
        patch(f"{BRANCH_INFO_MODULE}.IssueManager"),
        patch(
            f"{BRANCH_INFO_MODULE}.get_all_cached_issues",
            return_value=[issue],
        ),
    ):
        info = get_branch_info(PROJECT_DIR)

    assert info.issue_status_label == expected_label


# ---------------------------------------------------------------------------
# get_branch_only
# ---------------------------------------------------------------------------


def test_get_branch_only_no_git_repo_returns_empty() -> None:
    with patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=False):
        info = get_branch_only(PROJECT_DIR)

    assert info == BranchInfo(
        is_git_repo=False,
        branch_name=None,
        is_dirty=False,
        issue_number=None,
        issue_title=None,
        issue_status_label=None,
        cache_last_checked=None,
    )


def test_get_branch_only_branch_with_issue_number() -> None:
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.get_current_branch_name",
            return_value="42-feature",
        ),
        patch(f"{BRANCH_INFO_MODULE}.is_working_directory_clean", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=42,
        ),
    ):
        info = get_branch_only(PROJECT_DIR)

    assert info.is_git_repo is True
    assert info.branch_name == "42-feature"
    assert info.is_dirty is False
    assert info.issue_number == 42
    assert info.issue_title is None
    assert info.issue_status_label is None
    assert info.cache_last_checked is None


def test_get_branch_only_branch_without_issue_number() -> None:
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(f"{BRANCH_INFO_MODULE}.get_current_branch_name", return_value="main"),
        patch(f"{BRANCH_INFO_MODULE}.is_working_directory_clean", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=None,
        ),
    ):
        info = get_branch_only(PROJECT_DIR)

    assert info.is_git_repo is True
    assert info.branch_name == "main"
    assert info.issue_number is None
    assert info.issue_title is None
    assert info.issue_status_label is None
    assert info.cache_last_checked is None


def test_get_branch_only_skips_github_and_cache_io() -> None:
    sentinel = Mock(side_effect=AssertionError("must not be called"))
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.get_current_branch_name",
            return_value="42-feature",
        ),
        patch(f"{BRANCH_INFO_MODULE}.is_working_directory_clean", return_value=True),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=42,
        ),
        patch(f"{BRANCH_INFO_MODULE}.get_repository_identifier", side_effect=sentinel),
        patch(f"{BRANCH_INFO_MODULE}.get_cache_file_path", side_effect=sentinel),
        patch(f"{BRANCH_INFO_MODULE}.load_cache_file", side_effect=sentinel),
        patch(f"{BRANCH_INFO_MODULE}.IssueManager", side_effect=sentinel),
        patch(f"{BRANCH_INFO_MODULE}.get_all_cached_issues", side_effect=sentinel),
    ):
        info = get_branch_only(PROJECT_DIR)

    assert info.is_git_repo is True
    assert info.branch_name == "42-feature"
    assert info.issue_number == 42


@pytest.mark.parametrize("clean_flag,expected_is_dirty", [(True, False), (False, True)])
def test_get_branch_only_dirty_flag(clean_flag: bool, expected_is_dirty: bool) -> None:
    with (
        patch(f"{BRANCH_INFO_MODULE}.is_git_repository", return_value=True),
        patch(f"{BRANCH_INFO_MODULE}.get_current_branch_name", return_value="main"),
        patch(
            f"{BRANCH_INFO_MODULE}.is_working_directory_clean",
            return_value=clean_flag,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.extract_issue_number_from_branch",
            return_value=None,
        ),
    ):
        info = get_branch_only(PROJECT_DIR)

    assert info.is_dirty is expected_is_dirty


# ---------------------------------------------------------------------------
# get_pr_for_issue
# ---------------------------------------------------------------------------


def test_get_pr_for_issue_two_step_lookup() -> None:
    repo_id = _fake_repo_id()
    branch_mgr = MagicMock()
    branch_mgr.get_branch_with_pr_fallback.return_value = "123-feature"
    pr_mgr = MagicMock()
    pr_mgr.find_pull_request_by_head.return_value = [{"number": 42, "url": "u"}]

    with (
        patch(
            f"{BRANCH_INFO_MODULE}.get_repository_identifier",
            return_value=repo_id,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.IssueBranchManager",
            return_value=branch_mgr,
        ) as branch_cls,
        patch(
            f"{BRANCH_INFO_MODULE}.PullRequestManager",
            return_value=pr_mgr,
        ),
    ):
        result = get_pr_for_issue(PROJECT_DIR, 42)

    assert result == 42
    branch_cls.assert_called_once_with(
        project_dir=PROJECT_DIR, repo_url=repo_id.https_url
    )
    branch_mgr.get_branch_with_pr_fallback.assert_called_once_with(
        42, repo_id.owner, repo_id.repo_name
    )
    pr_mgr.find_pull_request_by_head.assert_called_once_with("123-feature")


def test_get_pr_for_issue_returns_none_when_no_branch_link() -> None:
    repo_id = _fake_repo_id()
    branch_mgr = MagicMock()
    branch_mgr.get_branch_with_pr_fallback.return_value = None
    pr_mgr = MagicMock()

    with (
        patch(
            f"{BRANCH_INFO_MODULE}.get_repository_identifier",
            return_value=repo_id,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.IssueBranchManager",
            return_value=branch_mgr,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.PullRequestManager",
            return_value=pr_mgr,
        ),
    ):
        result = get_pr_for_issue(PROJECT_DIR, 42)

    assert result is None
    pr_mgr.find_pull_request_by_head.assert_not_called()


def test_get_pr_for_issue_returns_none_when_no_open_pr() -> None:
    repo_id = _fake_repo_id()
    branch_mgr = MagicMock()
    branch_mgr.get_branch_with_pr_fallback.return_value = "branch"
    pr_mgr = MagicMock()
    pr_mgr.find_pull_request_by_head.return_value = []

    with (
        patch(
            f"{BRANCH_INFO_MODULE}.get_repository_identifier",
            return_value=repo_id,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.IssueBranchManager",
            return_value=branch_mgr,
        ),
        patch(
            f"{BRANCH_INFO_MODULE}.PullRequestManager",
            return_value=pr_mgr,
        ),
    ):
        result = get_pr_for_issue(PROJECT_DIR, 42)

    assert result is None


def test_get_pr_for_issue_no_repo_remote() -> None:
    sentinel = Mock(side_effect=AssertionError("must not be called"))
    with (
        patch(f"{BRANCH_INFO_MODULE}.get_repository_identifier", return_value=None),
        patch(f"{BRANCH_INFO_MODULE}.IssueBranchManager", side_effect=sentinel),
        patch(f"{BRANCH_INFO_MODULE}.PullRequestManager", side_effect=sentinel),
    ):
        result = get_pr_for_issue(PROJECT_DIR, 42)

    assert result is None
