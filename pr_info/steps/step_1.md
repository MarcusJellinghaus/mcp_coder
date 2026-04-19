# Step 1: Create shim module + smoke test

> **Read `pr_info/steps/summary.md` first for full context.**

## Goal

Create the shim module `mcp_workspace_git.py` and its smoke test. This step adds new files only — no existing files are modified.

## WHERE

- Create: `src/mcp_coder/mcp_workspace_git.py`
- Create: `tests/test_mcp_workspace_git_smoke.py`

## WHAT — Shim module

Pure re-export file. No logic, no wrapper functions. Imports 28 symbols + 1 constant from `mcp_workspace.git_operations` submodules and re-exports them.

```python
"""Thin shim re-exporting git operations from mcp_workspace."""

# Core
from mcp_workspace.git_operations.core import CommitResult, _safe_repo_context

# Repository status
from mcp_workspace.git_operations.repository_status import (
    get_full_status,
    is_git_repository,
    is_working_directory_clean,
)

# Branch queries
from mcp_workspace.git_operations.branch_queries import (
    branch_exists,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    has_remote_tracking_branch,
    validate_branch_name,
)

# Branches
from mcp_workspace.git_operations.branches import checkout_branch, create_branch, delete_branch

# Commits
from mcp_workspace.git_operations.commits import commit_staged_files, get_latest_commit_sha

# Diffs
from mcp_workspace.git_operations.diffs import get_branch_diff, get_git_diff_for_commit

# Compact diffs
from mcp_workspace.git_operations.compact_diffs import get_compact_diff

# Remotes
from mcp_workspace.git_operations.remotes import (
    fetch_remote,
    get_github_repository_url,
    git_push,
    push_branch,
    rebase_onto_branch,
)

# Staging
from mcp_workspace.git_operations.staging import stage_all_changes

# Workflows
from mcp_workspace.git_operations.workflows import commit_all_changes, needs_rebase

# Parent branch detection
from mcp_workspace.git_operations.parent_branch_detection import (
    MERGE_BASE_DISTANCE_THRESHOLD,
    detect_parent_branch_via_merge_base,
)

__all__ = [
    "CommitResult",
    "_safe_repo_context",
    "get_full_status",
    "is_git_repository",
    "is_working_directory_clean",
    "branch_exists",
    "extract_issue_number_from_branch",
    "get_current_branch_name",
    "get_default_branch_name",
    "has_remote_tracking_branch",
    "validate_branch_name",
    "checkout_branch",
    "create_branch",
    "delete_branch",
    "commit_staged_files",
    "get_latest_commit_sha",
    "get_branch_diff",
    "get_git_diff_for_commit",
    "get_compact_diff",
    "fetch_remote",
    "get_github_repository_url",
    "git_push",
    "push_branch",
    "rebase_onto_branch",
    "stage_all_changes",
    "commit_all_changes",
    "needs_rebase",
    "MERGE_BASE_DISTANCE_THRESHOLD",
    "detect_parent_branch_via_merge_base",
]
```

## WHAT — Smoke test

```python
"""Smoke test for mcp_workspace_git shim."""

def test_shim_importable() -> None:
    """Shim module can be imported."""
    import mcp_coder.mcp_workspace_git

def test_key_symbols_accessible() -> None:
    """Key symbols are accessible from shim."""
    from mcp_coder.mcp_workspace_git import (
        CommitResult,
        checkout_branch,
        commit_all_changes,
        get_current_branch_name,
        get_full_status,
        git_push,
        MERGE_BASE_DISTANCE_THRESHOLD,
    )
    assert CommitResult is not None
    assert callable(checkout_branch)
    assert callable(commit_all_changes)
    assert isinstance(MERGE_BASE_DISTANCE_THRESHOLD, int)

def test_all_exports_defined() -> None:
    """__all__ has expected count."""
    from mcp_coder.mcp_workspace_git import __all__
    assert len(__all__) == 29  # 28 symbols + 1 constant
```

## HOW

- No integration points — standalone new files
- Smoke test runs without markers (fast, no git repo needed)

## ALGORITHM

```
1. Create shim file with grouped imports from mcp_workspace.git_operations submodules
2. Create smoke test verifying importability and symbol accessibility
3. Run pytest on smoke test only
4. Run pylint + mypy on new files
5. Commit: "feat: add mcp_workspace_git shim module with smoke test"
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Create the shim module src/mcp_coder/mcp_workspace_git.py and its smoke test
tests/test_mcp_workspace_git_smoke.py exactly as specified. Do NOT modify any
existing files. Run the smoke test, then run pylint and mypy checks.
Commit with message: "feat: add mcp_workspace_git shim module with smoke test"
```
