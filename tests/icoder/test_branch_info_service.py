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


def test_start_pr_fetch_increments_generation() -> None:
    """Successive start_pr_fetch calls return monotonically increasing tokens."""
    service = BranchInfoService(PROJECT_DIR)
    assert service.current_pr_fetch_generation == 0
    assert service.start_pr_fetch() == 1
    assert service.start_pr_fetch() == 2
    assert service.current_pr_fetch_generation == 2


def test_set_pr_enabled_false_increments_generation() -> None:
    """Toggling PR off bumps the generation, invalidating in-flight workers."""
    service = BranchInfoService(PROJECT_DIR)
    service.set_pr_enabled(True)
    gen_after_on = service.current_pr_fetch_generation
    service.set_pr_enabled(False)
    assert service.current_pr_fetch_generation == gen_after_on + 1


def test_set_pr_enabled_true_does_not_increment() -> None:
    """Toggling PR on does NOT bump the generation."""
    service = BranchInfoService(PROJECT_DIR)
    gen_before = service.current_pr_fetch_generation
    service.set_pr_enabled(True)
    assert service.current_pr_fetch_generation == gen_before
    service.set_pr_enabled(True)
    assert service.current_pr_fetch_generation == gen_before


def test_fetch_branch_only_delegates_to_data_layer() -> None:
    """fetch_branch_only calls get_branch_only(project_dir) and returns its result."""
    service = BranchInfoService(PROJECT_DIR)
    info = _make_info()
    with patch(f"{ADAPTER_MODULE}.get_branch_only", return_value=info) as mock_fn:
        result = service.fetch_branch_only()
    mock_fn.assert_called_once_with(PROJECT_DIR)
    assert result is info


def test_begin_quick_tick_returns_false_when_in_flight() -> None:
    """Second begin_quick_tick call returns False; resets after end_quick_tick."""
    service = BranchInfoService(PROJECT_DIR)
    assert service.begin_quick_tick() is True
    assert service.begin_quick_tick() is False
    service.end_quick_tick()
    assert service.begin_quick_tick() is True


def test_begin_full_tick_returns_false_when_in_flight() -> None:
    """Second begin_full_tick call returns False; resets after end_full_tick."""
    service = BranchInfoService(PROJECT_DIR)
    assert service.begin_full_tick() is True
    assert service.begin_full_tick() is False
    service.end_full_tick()
    assert service.begin_full_tick() is True


def test_quick_and_full_tick_guards_are_independent() -> None:
    """Quick tick and full tick guards do not block each other."""
    service = BranchInfoService(PROJECT_DIR)
    assert service.begin_quick_tick() is True
    assert service.begin_full_tick() is True

    service2 = BranchInfoService(PROJECT_DIR)
    assert service2.begin_full_tick() is True
    assert service2.begin_quick_tick() is True


def test_periodic_tick_guards_independent_of_manual_refresh() -> None:
    """Tick guards and manual issue/PR fetch flags do not block each other."""
    service = BranchInfoService(PROJECT_DIR)
    service.begin_quick_tick()
    assert service.begin_issue_fetch() is True
    assert service.begin_pr_fetch() is True

    service2 = BranchInfoService(PROJECT_DIR)
    service2.begin_full_tick()
    assert service2.begin_issue_fetch() is True
    assert service2.begin_pr_fetch() is True

    service3 = BranchInfoService(PROJECT_DIR)
    service3.begin_issue_fetch()
    service3.begin_pr_fetch()
    assert service3.begin_quick_tick() is True
    assert service3.begin_full_tick() is True
