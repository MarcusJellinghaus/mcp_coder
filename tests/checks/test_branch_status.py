"""Shim-contract tests for mcp_coder.checks.branch_status.

The module is a thin re-export of mcp_workspace.checks.* (issue #1068). These
tests assert only the shim contract — the re-export surface and the presence of
the upstream #244 markers. Upstream internals (rendering, recommendation
wording, CI parsing) are covered by mcp-workspace's own suite and are NOT
re-tested here.
"""

import dataclasses

import mcp_coder.checks.branch_status as branch_status
from mcp_coder.checks.branch_status import (
    BranchStatusReport,
    CIStatus,
    collect_branch_status,
    create_empty_report,
    get_failed_jobs_summary,
)


def test_shim_reexports_expected_names() -> None:
    """Every name in __all__ is importable and of the expected kind."""
    assert isinstance(branch_status.GITHUB_TOKEN_HINT, str)
    assert isinstance(CIStatus.PASSED, CIStatus)
    assert isinstance(BranchStatusReport, type)
    assert callable(collect_branch_status)
    assert callable(create_empty_report)
    assert callable(get_failed_jobs_summary)


def test_ci_status_has_degradation_members() -> None:
    """CIStatus carries the #244 degradation members."""
    assert CIStatus.UNAVAILABLE
    assert CIStatus.UNKNOWN


def test_report_has_pr_feedback_fields() -> None:
    """BranchStatusReport exposes the #244 PR-feedback fields."""
    field_names = {f.name for f in dataclasses.fields(BranchStatusReport)}
    assert "pr_feedback_text" in field_names
    assert "pr_feedback_blocks_merge" in field_names
    assert "pr_feedback_undeterminable" in field_names


def test_collect_pr_feedback_not_reexported() -> None:
    """collect_pr_feedback is intentionally not part of the shim surface."""
    assert not hasattr(branch_status, "collect_pr_feedback")
