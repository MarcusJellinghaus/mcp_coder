"""Smoke test for mcp_workspace_github shim."""


def test_shim_importable() -> None:
    """Shim module can be imported."""
    import mcp_coder.mcp_workspace_github  # noqa: F401


def test_key_symbols_accessible() -> None:
    """Key symbols are accessible from shim."""
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

    assert BaseGitHubManager is not None
    assert CIResultsManager is not None
    assert IssueManager is not None
    assert LabelsManager is not None
    assert PullRequestManager is not None
    assert RepoIdentifier is not None
    assert callable(get_authenticated_username)
    assert callable(parse_github_url)
    assert PullRequestData is not None


def test_all_exports_defined() -> None:
    """__all__ has expected count."""
    from mcp_coder.mcp_workspace_github import __all__

    assert len(__all__) == 34
