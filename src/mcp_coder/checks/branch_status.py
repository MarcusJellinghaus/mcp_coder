"""Thin shim re-exporting branch-status from mcp_workspace.

The fork was collapsed onto mcp_workspace.checks.* (issue #1068). Only names
actually consumed by mcp-coder callers/tests are re-exported. collect_pr_feedback
is intentionally NOT re-exported — consumers reach PR feedback transitively via
collect_branch_status's report fields.
"""

from typing import List

from mcp_workspace.checks.branch_status import (
    BranchStatusReport,
    collect_branch_status,
    create_empty_report,
    get_failed_jobs_summary,
)
from mcp_workspace.checks.branch_status_rendering import GITHUB_TOKEN_HINT, CIStatus

__all__: List[str] = [
    "BranchStatusReport",
    "collect_branch_status",
    "create_empty_report",
    "get_failed_jobs_summary",
    "CIStatus",
    "GITHUB_TOKEN_HINT",
]
