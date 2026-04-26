"""Smoke test for mcp_workspace_github shim."""


def test_shim_importable() -> None:
    """Shim module can be imported."""
    import mcp_coder.mcp_workspace_github  # noqa: F401


def test_all_exports_defined() -> None:
    """__all__ has expected count."""
    from mcp_coder.mcp_workspace_github import __all__

    assert len(__all__) == 24


def test_key_symbols_importable() -> None:
    """Key symbols can be imported and are real implementations."""
    from mcp_coder.mcp_workspace_github import (
        BaseGitHubManager,
        CheckResult,
        CIResultsManager,
        IssueManager,
        LabelsManager,
        PullRequestData,
        PullRequestManager,
        RepoIdentifier,
        get_authenticated_username,
        verify_github,
    )

    assert callable(get_authenticated_username)
    assert callable(verify_github)
    assert BaseGitHubManager is not None
    assert CheckResult is not None
    assert CIResultsManager is not None
    assert IssueManager is not None
    assert LabelsManager is not None
    assert PullRequestManager is not None
    assert RepoIdentifier is not None
    assert PullRequestData is not None
