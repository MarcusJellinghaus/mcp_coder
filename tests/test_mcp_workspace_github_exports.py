"""Tests for the public surface of the mcp_workspace_github shim."""

import pytest

import mcp_coder.mcp_workspace_github as shim


def test_get_issue_cache_last_checked_is_exported() -> None:
    from mcp_coder.mcp_workspace_github import get_issue_cache_last_checked

    assert callable(get_issue_cache_last_checked)
    assert "get_issue_cache_last_checked" in shim.__all__


@pytest.mark.parametrize(
    "name",
    [
        "get_cache_file_path",
        "load_cache_file",
        "save_cache_file",
        "log_stale_cache_entries",
    ],
)
def test_underscore_cache_aliases_removed(name: str) -> None:
    assert not hasattr(shim, name)
    assert name not in shim.__all__


@pytest.mark.parametrize("name", ["GitHubRateLimitError", "to_rate_limit_error"])
def test_rate_limit_names_exported(name: str) -> None:
    assert hasattr(shim, name)
    assert name in shim.__all__


@pytest.mark.parametrize("name", ["PullRequestCache", "OpenPullRequest"])
def test_pull_request_cache_names_exported(name: str) -> None:
    assert hasattr(shim, name)
    assert name in shim.__all__


@pytest.mark.parametrize(
    "name", ["BranchLookupCache", "BranchLookup", "BranchLookupError"]
)
def test_branch_lookup_names_exported(name: str) -> None:
    assert hasattr(shim, name)
    assert name in shim.__all__
