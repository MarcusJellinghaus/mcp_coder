"""Test factory for IssueData.

One place that builds issue dicts for tests, so upstream field additions
need no test changes: the base dict comes from create_empty_issue_data().
"""

from typing import Any, cast

from mcp_coder.mcp_workspace_github import IssueData, create_empty_issue_data


def make_issue_data(**overrides: Any) -> IssueData:
    """Build a full IssueData for tests; overrides replace defaults."""
    unknown = overrides.keys() - IssueData.__annotations__.keys()
    if unknown:
        raise TypeError(f"Unknown IssueData keys: {sorted(unknown)}")
    merged: dict[str, Any] = {
        **create_empty_issue_data(),
        "number": 1,
        "state": "open",
        **overrides,
    }
    if "title" not in overrides:
        merged["title"] = f"Issue {merged['number']}"
    if "url" not in overrides:
        merged["url"] = f"https://github.com/owner/repo/issues/{merged['number']}"
    return cast(IssueData, merged)
