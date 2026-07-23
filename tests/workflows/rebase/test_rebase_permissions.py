"""Unit tests for the least-privilege REBASE_LLM_PERMISSIONS constant."""

from mcp_coder.workflows.rebase_permissions import REBASE_LLM_PERMISSIONS


def test_allow_list_is_non_empty_list() -> None:
    """The permissions.allow entry must be a non-empty list."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert isinstance(allow, list)
    assert len(allow) > 0


def test_allow_list_contains_git_write_ops() -> None:
    """The allow-list must grant exactly the git-write ops the session needs."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    for entry in (
        "Bash(git rebase:*)",
        "Bash(git add:*)",
        "Bash(git commit:*)",
        "Bash(git checkout --theirs:*)",
        "Bash(git restore:*)",
        "Bash(git remote get-url:*)",
    ):
        assert entry in allow


def test_allow_list_excludes_push() -> None:
    """Python performs the force-push; the LLM gets no push grant."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all("push" not in entry for entry in allow)


def test_allow_list_excludes_uv_lock() -> None:
    """Lockfile handling is out of scope for this repo."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all("uv lock" not in entry for entry in allow)
