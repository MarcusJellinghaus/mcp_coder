# Step 2: Flip shim imports to `mcp_workspace.git_operations`

## Context
See [summary.md](summary.md) for full issue context.

After step 1, `_safe_repo_context` has zero consumers. The shim can now be flipped to import from the external `mcp_workspace.git_operations` package, and `_safe_repo_context` can be dropped.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/mcp_workspace_git.py` | Modify |
| `tests/test_mcp_workspace_git_smoke.py` | Modify |

## WHAT

### `mcp_workspace_git.py`
- Change every `from mcp_coder.utils.git_operations.*` import to `from mcp_workspace.git_operations.*`
- Remove the `_safe_repo_context` import and `__all__` entry
- Update module docstring
- Add comment noting git functionality lives in `mcp_workspace`

### `test_mcp_workspace_git_smoke.py`
- Change `len(__all__) == 29` assertion to `len(__all__) == 28`

## HOW

### Full import mapping (shim file)

```python
# BEFORE                                              # AFTER
from mcp_coder.utils.git_operations.branch_queries    → from mcp_workspace.git_operations.branch_queries
from mcp_coder.utils.git_operations.branches          → from mcp_workspace.git_operations.branches
from mcp_coder.utils.git_operations.commits           → from mcp_workspace.git_operations.commits
from mcp_coder.utils.git_operations.compact_diffs     → from mcp_workspace.git_operations.compact_diffs
from mcp_coder.utils.git_operations.core              → from mcp_workspace.git_operations.core
from mcp_coder.utils.git_operations.diffs             → from mcp_workspace.git_operations.diffs
from mcp_coder.utils.git_operations.parent_branch_detection → from mcp_workspace.git_operations.parent_branch_detection
from mcp_coder.utils.git_operations.remotes           → from mcp_workspace.git_operations.remotes
from mcp_coder.utils.git_operations.repository_status → from mcp_workspace.git_operations.repository_status
from mcp_coder.utils.git_operations.staging           → from mcp_workspace.git_operations.staging
from mcp_coder.utils.git_operations.workflows         → from mcp_workspace.git_operations.workflows
```

### Symbols dropped
- `_safe_repo_context` — removed from `core` import and from `__all__`

### `__all__` count
- Before: 29 (28 symbols + `_safe_repo_context`)
- After: 28 (28 symbols, no `_safe_repo_context`)

## ALGORITHM

No logic changes — pure import path replacement.

## DATA

No data structure changes. All 28 re-exported symbols remain identical.

## New docstring and comment

```python
"""Thin shim re-exporting git operations from mcp_workspace.

Centralises all git operation imports into a single module.
All mcp_coder code must import git operations through this shim.

Git functionality lives in the mcp_workspace package.
File issues or feature requests there: MarcusJellinghaus/mcp-workspace
"""
```

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement pr_info/steps/step_2.md.

Flip the git shim to import from the external mcp_workspace package:
1. In `src/mcp_coder/mcp_workspace_git.py`, change all imports from
   `mcp_coder.utils.git_operations.*` to `mcp_workspace.git_operations.*`
2. Drop `_safe_repo_context` from both the import and `__all__`
3. Update the module docstring and add comment about mcp_workspace
4. In `tests/test_mcp_workspace_git_smoke.py`, change assertion from 29 to 28
5. Run all checks (pylint, mypy, pytest)
```

## Commit message
```
refactor: flip git shim to mcp_workspace.git_operations (#886)

Change all imports in mcp_workspace_git.py from the local
mcp_coder.utils.git_operations to the external
mcp_workspace.git_operations package. Drop _safe_repo_context
(no consumers remain after previous commit).
```
