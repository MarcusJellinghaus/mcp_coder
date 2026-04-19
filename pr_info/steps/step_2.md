# Step 2: Update all source consumers to use shim

> **Read `pr_info/steps/summary.md` first for full context.**

## Goal

Switch every `src/` file that imports from `mcp_coder.utils.git_operations` (or its submodules) to import from `mcp_coder.mcp_workspace_git` instead. Also update `utils/__init__.py` to source surviving git re-exports from the shim and remove dead symbols.

## WHERE — Files to modify

### Direct submodule imports → shim

| File | Old import path | Symbols |
|------|----------------|---------|
| `src/mcp_coder/checks/branch_status.py` | `utils.git_operations` + `.branch_queries` | `needs_rebase`, `extract_issue_number_from_branch`, `get_current_branch_name` |
| `src/mcp_coder/cli/commands/git_tool.py` | `utils.git_operations.compact_diffs` + `.diffs` | `get_compact_diff`, `get_git_diff_for_commit` |
| `src/mcp_coder/cli/commands/commit.py` | `utils.git_operations` | `commit_staged_files`, `get_git_diff_for_commit`, `is_git_repository`, `stage_all_changes` |
| `src/mcp_coder/cli/commands/check_branch_status.py` | `utils.git_operations.branch_queries` | `get_current_branch_name`, `has_remote_tracking_branch` |
| `src/mcp_coder/workflows/create_pr/core.py` | `utils.git_operations.branch_queries` | `extract_issue_number_from_branch` |
| `src/mcp_coder/workflows/create_plan/core.py` | `utils.git_operations.remotes` + `.repository_status` + `.workflows` | `git_push`, `is_working_directory_clean`, `commit_all_changes` |
| `src/mcp_coder/workflows/create_plan/prerequisites.py` | `utils.git_operations.branches` | `checkout_branch` |
| `src/mcp_coder/workflows/implement/core.py` | `utils.git_operations` + `.branch_queries` | `get_current_branch_name`, `rebase_onto_branch`, `extract_issue_number_from_branch` |
| `src/mcp_coder/workflows/implement/ci_operations.py` | `utils.git_operations.commits` | `get_latest_commit_sha` |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | `utils.git_operations` | `checkout_branch`, `fetch_remote` |
| `src/mcp_coder/workflow_utils/commit_operations.py` | `utils.git_operations` | `get_git_diff_for_commit`, `stage_all_changes` |
| `src/mcp_coder/workflow_utils/base_branch.py` | `utils.git_operations` | `MERGE_BASE_DISTANCE_THRESHOLD`, `detect_parent_branch_via_merge_base`, `extract_issue_number_from_branch`, `get_current_branch_name`, `get_default_branch_name` |
| `src/mcp_coder/utils/git_utils.py` | `.git_operations` | `get_current_branch_name` |

### `utils/__init__.py` — source from shim + remove dead symbols

**Surviving re-exports** (source from `mcp_coder.mcp_workspace_git`):
`CommitResult`, `branch_exists`, `checkout_branch`, `commit_all_changes`, `commit_staged_files`, `fetch_remote`, `get_branch_diff`, `get_current_branch_name`, `get_default_branch_name`, `get_full_status`, `get_git_diff_for_commit`, `get_github_repository_url`, `git_push`, `is_working_directory_clean`, `stage_all_changes`

**Dead symbols to remove** (not in shim, no external consumers):
`create_branch`, `git_move`, `is_file_tracked`, `push_branch`, `is_git_repository`, `get_staged_changes`, `get_unstaged_changes`, `stage_specific_files`, `PushResult`

Note on `is_git_repository`: it's used in `cli/commands/commit.py` — that file imports it from `utils.git_operations` directly, which we change to import from the shim. But `is_git_repository` is NOT in the shim's 24 symbols. Check: the issue lists it as a dead symbol. If `commit.py` uses it, either add it to the shim or replace the usage. **Resolution**: `is_git_repository` is used in `commit.py` — it must be added to the shim, OR `commit.py` must stop using it. Per the issue's dead symbol list, it should be removed. Check `commit.py` usage and handle accordingly (likely the check is redundant since commit operations will fail naturally on non-git dirs).

### `__init__.py` (root) — source from shim

Change:
```python
from .utils.git_operations import (CommitResult, commit_all_changes, ...)
```
To:
```python
from .mcp_workspace_git import (CommitResult, commit_all_changes, ...)
```

Note: `is_git_repository` is in root `__all__` — remove it (dead symbol per issue).

## WHAT — The transformation pattern

Every import like:
```python
from mcp_coder.utils.git_operations import X, Y
from mcp_coder.utils.git_operations.submodule import Z
from ...utils.git_operations import X
from ...utils.git_operations.submodule import Z
from .git_operations import X
```

Becomes:
```python
from mcp_coder.mcp_workspace_git import X, Y, Z
```

For relative imports, use the appropriate relative form:
```python
from ...mcp_workspace_git import X  # if in src/mcp_coder/some/nested/module.py — NO
```
Actually: since `mcp_workspace_git.py` is at `src/mcp_coder/mcp_workspace_git.py`, use absolute imports for clarity in deeply nested files. Relative only works cleanly for `utils/git_utils.py` (sibling → parent).

## ALGORITHM

```
1. For each file in the table above:
     Replace old git_operations import with: from mcp_coder.mcp_workspace_git import <symbols>
2. Update utils/__init__.py:
     Replace `from .git_operations import (...)` with `from mcp_coder.mcp_workspace_git import (...)`
     Remove dead symbols from import and __all__
3. Update root __init__.py:
     Replace `from .utils.git_operations import (...)` with `from .mcp_workspace_git import (...)`
     Remove is_git_repository from import and __all__
4. Run pylint, mypy, pytest (unit tests only)
5. Commit: "refactor: switch all source imports to mcp_workspace_git shim"
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Update all source files listed in the step to import from mcp_coder.mcp_workspace_git
instead of mcp_coder.utils.git_operations. Update utils/__init__.py to source
surviving git re-exports from the shim and remove dead symbols. Update root
__init__.py similarly. Do NOT delete the old git_operations directory yet (it
still exists for now). Run pylint, mypy, and pytest checks.
Commit with message: "refactor: switch all source imports to mcp_workspace_git shim"
```
