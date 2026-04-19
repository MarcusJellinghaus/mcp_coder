"""Smoke test for mcp_workspace_git shim."""


def test_shim_importable() -> None:
    """Shim module can be imported."""
    import mcp_coder.mcp_workspace_git  # noqa: F401


def test_key_symbols_accessible() -> None:
    """Key symbols are accessible from shim."""
    from mcp_coder.mcp_workspace_git import (
        MERGE_BASE_DISTANCE_THRESHOLD,
        CommitResult,
        checkout_branch,
        commit_all_changes,
        get_current_branch_name,
        get_full_status,
        git_push,
    )

    assert CommitResult is not None
    assert callable(checkout_branch)
    assert callable(commit_all_changes)
    assert isinstance(MERGE_BASE_DISTANCE_THRESHOLD, int)


def test_all_exports_defined() -> None:
    """__all__ has expected count."""
    from mcp_coder.mcp_workspace_git import __all__

    assert len(__all__) == 29  # 28 symbols + 1 constant
