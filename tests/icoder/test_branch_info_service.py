"""Tests for the BranchInfoService adapter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from mcp_coder.icoder.services.branch_info_service import BranchInfoService
from mcp_coder.services.branch_info import BranchInfo

PROJECT_DIR = Path("/fake/project")

ADAPTER_MODULE = "mcp_coder.icoder.services.branch_info_service"


def _make_info() -> BranchInfo:
    return BranchInfo(
        is_git_repo=True,
        branch_name="main",
        is_dirty=False,
        issue_number=None,
        issue_title=None,
        issue_status_label=None,
        cache_last_checked=None,
    )


def test_initial_state_pr_disabled_and_no_branch() -> None:
    """Initial state: pr disabled, branch_changed(None) returns False."""
    service = BranchInfoService(PROJECT_DIR)
    assert service.pr_enabled is False
    assert service.branch_changed(None) is False


def test_set_pr_enabled_toggles() -> None:
    """set_pr_enabled flips the toggle in both directions."""
    service = BranchInfoService(PROJECT_DIR)
    service.set_pr_enabled(True)
    assert service.pr_enabled is True
    service.set_pr_enabled(False)
    assert service.pr_enabled is False


def test_begin_issue_fetch_returns_false_when_in_flight() -> None:
    """Second begin_issue_fetch call returns False if no end was called."""
    service = BranchInfoService(PROJECT_DIR)
    assert service.begin_issue_fetch() is True
    assert service.begin_issue_fetch() is False


def test_end_issue_fetch_resets_flag() -> None:
    """After end_issue_fetch, begin_issue_fetch can succeed again."""
    service = BranchInfoService(PROJECT_DIR)
    service.begin_issue_fetch()
    service.end_issue_fetch()
    assert service.begin_issue_fetch() is True


def test_begin_pr_fetch_independent_of_issue_fetch() -> None:
    """Issue in-flight does not block a PR fetch from beginning."""
    service = BranchInfoService(PROJECT_DIR)
    service.begin_issue_fetch()
    assert service.begin_pr_fetch() is True


def test_end_pr_fetch_resets_flag() -> None:
    """After end_pr_fetch, begin_pr_fetch can succeed again."""
    service = BranchInfoService(PROJECT_DIR)
    service.begin_pr_fetch()
    service.end_pr_fetch()
    assert service.begin_pr_fetch() is True


def test_branch_changed_detects_first_real_branch() -> None:
    """First call with None returns False; first non-None returns True."""
    service = BranchInfoService(PROJECT_DIR)
    assert service.branch_changed(None) is False
    assert service.branch_changed("main") is True
    assert service.branch_changed("main") is False


def test_branch_changed_detects_switch() -> None:
    """branch_changed returns True when branch name changes."""
    service = BranchInfoService(PROJECT_DIR)
    service.branch_changed("main")
    assert service.branch_changed("123-feature") is True


def test_fetch_info_delegates_to_data_layer() -> None:
    """fetch_info calls get_branch_info(project_dir) and returns its result."""
    service = BranchInfoService(PROJECT_DIR)
    info = _make_info()
    with patch(f"{ADAPTER_MODULE}.get_branch_info", return_value=info) as mock_fn:
        result = service.fetch_info()
    mock_fn.assert_called_once_with(PROJECT_DIR)
    assert result is info


def test_fetch_pr_delegates_to_data_layer() -> None:
    """fetch_pr calls get_pr_for_issue(project_dir, issue_number)."""
    service = BranchInfoService(PROJECT_DIR)
    with patch(f"{ADAPTER_MODULE}.get_pr_for_issue", return_value=99) as mock_fn:
        result = service.fetch_pr(42)
    mock_fn.assert_called_once_with(PROJECT_DIR, 42)
    assert result == 99
