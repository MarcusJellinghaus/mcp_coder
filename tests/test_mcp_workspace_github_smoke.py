"""Smoke test for mcp_workspace_github shim."""

import pytest

from mcp_coder.mcp_workspace_github import _AVAILABLE


def test_shim_importable() -> None:
    """Shim module can be imported even when upstream is missing."""
    import mcp_coder.mcp_workspace_github  # noqa: F401


def test_all_exports_defined() -> None:
    """__all__ has expected count."""
    from mcp_coder.mcp_workspace_github import __all__

    assert len(__all__) == 34


def test_names_importable_regardless_of_upstream() -> None:
    """All exported names can be imported (may be sentinels if upstream missing)."""
    from mcp_coder.mcp_workspace_github import (
        BaseGitHubManager,
        CIResultsManager,
        IssueManager,
        LabelsManager,
        PullRequestData,
        PullRequestManager,
        RepoIdentifier,
        get_authenticated_username,
        parse_github_url,
    )

    # Names are importable in either case
    assert BaseGitHubManager is not None
    assert CIResultsManager is not None
    assert IssueManager is not None
    assert LabelsManager is not None
    assert PullRequestManager is not None
    assert RepoIdentifier is not None
    assert PullRequestData is not None

    if _AVAILABLE:
        # Real implementations should be callable
        assert callable(get_authenticated_username)
        assert callable(parse_github_url)


@pytest.mark.github_integration
def test_key_symbols_are_real() -> None:
    """Key symbols are real implementations (requires mcp_workspace.github_operations)."""
    if not _AVAILABLE:
        pytest.skip("mcp_workspace.github_operations not installed")

    from mcp_coder.mcp_workspace_github import (
        BaseGitHubManager,
        CIResultsManager,
        IssueManager,
        LabelsManager,
        PullRequestData,
        PullRequestManager,
        RepoIdentifier,
        get_authenticated_username,
        parse_github_url,
    )

    assert callable(get_authenticated_username)
    assert callable(parse_github_url)
    assert BaseGitHubManager is not None
    assert CIResultsManager is not None
    assert IssueManager is not None
    assert LabelsManager is not None
    assert PullRequestManager is not None
    assert RepoIdentifier is not None
    assert PullRequestData is not None
