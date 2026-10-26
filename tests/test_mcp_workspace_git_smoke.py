"""Smoke test for mcp_workspace_git shim."""


def test_shim_importable() -> None:
    """Shim module can be imported."""
    import mcp_coder.mcp_workspace_git

    assert mcp_coder.mcp_workspace_git


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
    assert callable(get_current_branch_name)
    assert callable(get_full_status)
    assert callable(git_push)
    assert isinstance(MERGE_BASE_DISTANCE_THRESHOLD, int)


def test_all_exports_defined() -> None:
    """Every name in __all__ is unique and defined on the shim."""
    import mcp_coder.mcp_workspace_git as shim

    assert len(set(shim.__all__)) == len(shim.__all__)
    for name in shim.__all__:
        assert hasattr(shim, name), name
