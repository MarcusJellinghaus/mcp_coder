# Issue #813: Consume git_operations from mcp_workspace via shim (part 3 of 5)

## Goal

Replace `mcp_coder`'s local `utils/git_operations/` (13 files) with a single shim module (`mcp_workspace_git.py`) that re-exports symbols from `mcp_workspace.git_operations`. Delete the local copy entirely.

## Architectural Changes

### Before
```
mcp_coder.utils.git_operations/     ← 13 local files with all git logic
    __init__.py, core.py, branches.py, branch_queries.py, commits.py,
    compact_diffs.py, diffs.py, file_tracking.py, parent_branch_detection.py,
    remotes.py, repository_status.py, staging.py, workflows.py

Consumers import from:
  - mcp_coder.utils.git_operations (package __init__)
  - mcp_coder.utils.git_operations.<submodule> (direct submodule)
  - mcp_coder.utils (re-exports via __init__.py)
  - mcp_coder (re-exports via root __init__.py)
```

### After
```
mcp_coder.mcp_workspace_git         ← single shim file, pure re-exports
    imports from mcp_workspace.git_operations.* submodules

Consumers import from:
  - mcp_coder.mcp_workspace_git (all source + test consumers)
  - mcp_coder.utils (surviving re-exports, sourced from shim)
  - mcp_coder (public API re-exports, sourced from shim)
```

### Dependency flow change
```
Before: mcp_coder.* → mcp_coder.utils.git_operations.* → GitPython
After:  mcp_coder.* → mcp_coder.mcp_workspace_git → mcp_workspace.git_operations.* → GitPython
```

### Architecture config changes

**`.importlinter`** — 2 contracts removed, 2 added:
- REMOVE: `git_local` (git operations local independence — package deleted)
- REMOVE: `git_operations_internal_layering` (internal layering — package deleted)
- ADD: `mcp_workspace_git_isolation` — only `mcp_coder.mcp_workspace_git` may import `mcp_workspace.git_operations.*`
- UPDATE: `git_library_isolation` — GitPython forbidden from all `mcp_coder` (no exceptions, since GitPython now lives in mcp_workspace)

**`tach.toml`** — new `shim_workspace` layer:
- ADD layer `shim_workspace` between `infrastructure` and `foundation`
- MOVE `mcp_coder.mcp_tools_py` from `infrastructure` to `shim_workspace`
- ADD `mcp_coder.mcp_workspace_git` to `shim_workspace`
- No changes to `mcp_coder.utils` entry (git_operations was implicit under it)

### Dead symbols removed from `utils/__init__.py`

These symbols have no consumers outside `git_operations/` itself and are not in the shim:
`create_branch`, `git_move`, `is_file_tracked`, `push_branch`, `is_git_repository`,
`get_staged_changes`, `get_unstaged_changes`, `stage_specific_files`

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/mcp_workspace_git.py` | Shim: re-exports 24 symbols from `mcp_workspace.git_operations.*` |
| `tests/test_mcp_workspace_git_smoke.py` | Smoke test: shim importable, key symbols accessible |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/__init__.py` | Git imports sourced from shim instead of `utils.git_operations` |
| `src/mcp_coder/utils/__init__.py` | Git imports sourced from shim; dead symbols removed |
| `src/mcp_coder/utils/git_utils.py` | Import from shim |
| `src/mcp_coder/checks/branch_status.py` | Import from shim |
| `src/mcp_coder/cli/commands/git_tool.py` | Import from shim |
| `src/mcp_coder/cli/commands/commit.py` | Import from shim |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Import from shim |
| `src/mcp_coder/workflows/create_pr/core.py` | Import from shim |
| `src/mcp_coder/workflows/create_plan/core.py` | Import from shim |
| `src/mcp_coder/workflows/create_plan/prerequisites.py` | Import from shim |
| `src/mcp_coder/workflows/implement/core.py` | Import from shim |
| `src/mcp_coder/workflows/implement/ci_operations.py` | Import from shim |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Import from shim |
| `src/mcp_coder/workflow_utils/commit_operations.py` | Import from shim |
| `src/mcp_coder/workflow_utils/base_branch.py` | Import from shim |
| `tests/test_module_integration.py` | Update to test shim paths; remove old `git_operations` tests |
| `tests/utils/test_git_encoding_stress.py` | Import from shim |
| `.importlinter` | Remove 2 old contracts, add 2 new isolation contracts |
| `tach.toml` | Add `shim_workspace` layer, move `mcp_tools_py`, add `mcp_workspace_git` |

## Files/Directories Deleted

| Path | Reason |
|------|--------|
| `src/mcp_coder/utils/git_operations/` (entire directory, 13 files) | Replaced by shim → mcp_workspace |
| `tests/utils/git_operations/` (entire directory, 14 files) | Tests already moved to mcp_workspace |

## Implementation Steps

| Step | Commit | Description |
|------|--------|-------------|
| 0 | Pre-flight check | Verify `mcp_workspace.git_operations` is available; fail-fast if not |
| 1 | Shim + smoke test | Create shim module and smoke test |
| 2 | Update source consumers | Switch all `src/` imports to use shim |
| 3 | Update test consumers + delete old tests | Switch test imports; delete `tests/utils/git_operations/` |
| 4 | Delete local git_operations | Delete `src/mcp_coder/utils/git_operations/` |
| 5 | Update architecture configs | `.importlinter` and `tach.toml` changes |

## Constraints

- Import path is `mcp_workspace.git_operations` (top-level, not under `file_tools`)
- `_safe_repo_context` imported from `mcp_workspace.git_operations.core` (private, pragmatic)
- Only 6 of 24 symbols are in `mcp_workspace.git_operations.__init__`; rest need submodule imports
- Tests must also use the shim (import-linter enforced)
- Dependency: issue ② (mcp-workspace#98) must be complete first
