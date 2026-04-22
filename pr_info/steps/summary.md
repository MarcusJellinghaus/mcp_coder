# Issue #886: Flip git shim to mcp_workspace and delete local git_operations

## Summary

Flip the `mcp_workspace_git.py` shim to import from `mcp_workspace.git_operations.*` (the external package) instead of the local `mcp_coder.utils.git_operations.*`. Enforce all consumers to go through the shim, then delete the local git_operations package entirely.

## Architectural / Design Changes

### Before
```
mcp_coder code  ──imports──►  mcp_coder.utils.git_operations.*  (local, uses GitPython)
                                    ▲
mcp_workspace_git.py (shim) ────────┘  re-exports from local package
```
- The shim (`mcp_workspace_git.py`) re-exports 29 symbols from the **local** `mcp_coder.utils.git_operations` package
- 5 files bypass the shim and import directly from local git_operations
- `failure_handling.py` uses `_safe_repo_context` (raw GitPython context manager)
- GitPython (`git`/`gitdb`) is allowed via import-linter exception for `mcp_coder.utils.git_operations.**`
- 13 source files in `src/mcp_coder/utils/git_operations/`

### After
```
mcp_coder code  ──imports──►  mcp_coder.mcp_workspace_git  (shim, single import path)
                                    │
                                    ▼
                              mcp_workspace.git_operations.*  (external package)
```
- The shim re-exports 28 symbols from the **external** `mcp_workspace.git_operations` package
- `_safe_repo_context` dropped from shim (no consumers remain)
- All consumers import through the shim — no direct imports from external or local git_operations
- `failure_handling.py` uses `execute_command` (subprocess) for `get_diff_stat()`
- GitPython (`git`/`gitdb`) forbidden everywhere with **zero exceptions**
- `src/mcp_coder/utils/git_operations/` deleted entirely (13 files)
- `tests/utils/git_operations/` deleted (2 files, after upstream test migration)

### Key Design Decisions
| Decision | Rationale |
|----------|-----------|
| Shim stays permanently | Single point of change if upstream reorganises |
| All imports through shim | Consistent architecture, one import path |
| GitPython forbidden everywhere | No local git_operations = no legitimate `git` imports |
| `get_diff_stat` uses subprocess | Keeps GitPython isolation with zero exceptions |
| `_safe_repo_context` dropped | Upstream renamed to `safe_repo_context`; sole consumer refactored to subprocess |

## Files Modified

| File | Action | Step |
|------|--------|------|
| `src/mcp_coder/workflow_utils/failure_handling.py` | Modify (subprocess instead of GitPython) | 1 |
| `tests/workflow_utils/test_failure_handling.py` | Modify (update mocks) | 1 |
| `src/mcp_coder/mcp_workspace_git.py` | Modify (flip imports, drop `_safe_repo_context`, add comment) | 2 |
| `tests/test_mcp_workspace_git_smoke.py` | Modify (29 → 28) | 2 |
| `src/mcp_coder/utils/git_utils.py` | Modify (import via shim) | 3 |
| `src/mcp_coder/utils/github_operations/base_manager.py` | Modify (import via shim) | 3 |
| `src/mcp_coder/utils/github_operations/ci_results_manager.py` | Modify (import via shim) | 3 |
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Modify (import via shim) | 3 |
| `src/mcp_coder/utils/github_operations/issues/manager.py` | Modify (import via shim) | 3 |

## Files Deleted

| File/Folder | Step |
|-------------|------|
| `src/mcp_coder/utils/git_operations/` (13 files) | 4 |
| `tests/utils/git_operations/` (2 files) | 4 |

## Config Files Modified

| File | Action | Step |
|------|--------|------|
| `.importlinter` | Remove shim exception, remove GitPython exception, update TODO | 4 |
| `vulture_whitelist.py` | Remove `PushResult` and `stage_specific_files` entries | 4 |

## Implementation Steps Overview

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Refactor `failure_handling.py` — replace GitPython with subprocess | `refactor: replace GitPython with subprocess in get_diff_stat` |
| 2 | Flip shim imports to `mcp_workspace.git_operations` | `refactor: flip git shim to mcp_workspace.git_operations` |
| 3 | Fix 5 bypass files to import through shim | `refactor: route git imports through shim in 5 bypass files` |
| 4 | Delete local git_operations + cleanup configs | `refactor: delete local git_operations and clean up configs` |

## Constraints
- **Hard blocker for test deletion**: MarcusJellinghaus/mcp-workspace#135 must merge before deleting `tests/utils/git_operations/`. If not merged, step 4 deletes source files only and leaves test files with a TODO.
- **Subprocess isolation**: `failure_handling.py` must use `execute_command` from `subprocess_runner`, not raw `subprocess` (enforced by `.importlinter`).
- **Import-linter limitation**: grimp v2.11 cannot enforce shim-only access to `mcp_workspace.git_operations` (external subpackage paths invisible). Enforcement relies on code review + layered architecture contract.
