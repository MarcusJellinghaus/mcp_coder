"""Unit tests for the least-privilege REBASE_LLM_PERMISSIONS constant."""

from mcp_coder.workflows.rebase_permissions import REBASE_LLM_PERMISSIONS


def test_allow_list_is_non_empty_list() -> None:
    """The permissions.allow entry must be a non-empty list."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert isinstance(allow, list)
    assert len(allow) > 0


def test_allow_list_has_no_bash_grants() -> None:
    """Non-interactive sessions load no Bash tool, so Bash grants are dead."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all(not entry.startswith("Bash(") for entry in allow)


def test_allow_list_contains_mcp_tools() -> None:
    """The MCP git/file/check tools the session actually uses stay granted."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    for entry in (
        "mcp__mcp-workspace__git",
        "mcp__mcp-workspace__get_base_branch",
        "mcp__mcp-workspace__read_file",
        "mcp__mcp-workspace__save_file",
        "mcp__mcp-workspace__edit_file",
        "mcp__mcp-workspace__delete_this_file",
        "mcp__mcp-tools-py__run_format_code",
        "mcp__mcp-tools-py__run_pylint_check",
        "mcp__mcp-tools-py__run_pytest_check",
        "mcp__mcp-tools-py__run_mypy_check",
    ):
        assert entry in allow


def test_allow_list_excludes_reference_project_tools() -> None:
    """Least privilege: no reference-project tools are granted."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all("reference" not in entry for entry in allow)


def test_allow_list_excludes_push() -> None:
    """Python performs the force-push; the LLM gets no push grant."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all("push" not in entry for entry in allow)


def test_allow_list_excludes_uv_lock() -> None:
    """Lockfile handling is out of scope for this repo."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all("uv lock" not in entry for entry in allow)
