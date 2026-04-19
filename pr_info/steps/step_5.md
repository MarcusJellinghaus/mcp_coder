# Step 5: Update architecture configs

> **Read `pr_info/steps/summary.md` first for full context.**

## Goal

Update `.importlinter` and `tach.toml` to reflect the new architecture: git_operations package is gone, shim is the single entry point, GitPython is fully isolated behind mcp_workspace.

## WHERE

- Modify: `.importlinter`
- Modify: `tach.toml`

## WHAT — `.importlinter` changes

### Remove 2 contracts

1. **`git_local`** ("Git Operations Local Independence") — the `mcp_coder.utils.git_operations` source module no longer exists.

2. **`git_operations_internal_layering`** ("Git Operations Internal Layering") — internal layers of the deleted package.

### Add 1 new contract

**`mcp_workspace_git_isolation`** — only the shim may import from `mcp_workspace.git_operations`:
```ini
[importlinter:contract:mcp_workspace_git_isolation]
name = MCP Workspace Git Operations Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    mcp_workspace.git_operations
ignore_imports =
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.core
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.repository_status
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.branch_queries
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.branches
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.commits
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.diffs
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.compact_diffs
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.remotes
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.staging
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.workflows
    mcp_coder.mcp_workspace_git -> mcp_workspace.git_operations.parent_branch_detection
```

### Update 2 existing contracts

**`jenkins_independence`** — Change `mcp_coder.utils.git_operations` to `mcp_coder.mcp_workspace_git` in the `forbidden_modules` list.


**`git_library_isolation`** — GitPython now fully forbidden from `mcp_coder` (no exceptions):
```ini
[importlinter:contract:git_library_isolation]
name = GitPython Library Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    git
    gitdb
```
Remove the old `ignore_imports` line that allowed `mcp_coder.utils.git_operations.** -> git`.

## WHAT — `tach.toml` changes

### Modules needing `depends_on` for `mcp_workspace_git`

The following modules import (directly or transitively) from `mcp_coder.mcp_workspace_git` and need `{ path = "mcp_coder.mcp_workspace_git" }` added to their `depends_on`:

- `mcp_coder` (root) -- root `__init__.py` re-exports git symbols from shim
- `mcp_coder.cli` -- `cli/utils.py` and commands import from shim
- `mcp_coder.workflows` -- multiple workflow modules import from shim
- `mcp_coder.workflow_utils` -- `commit_operations.py`, `base_branch.py`, `failure_handling.py` import from shim
- `mcp_coder.checks` -- `branch_status.py` imports from shim
- `mcp_coder.utils` -- `utils/__init__.py` and `git_utils.py` source from shim
- `tests` -- test files import from shim

After making all changes, run `tach check` to verify boundaries are satisfied.

### Add new layer

Insert `shim_workspace` between `infrastructure` and `foundation`:
```toml
layers = [
    "presentation",
    "application",
    "tools",
    "domain",
    "infrastructure",
    "shim_workspace",
    "foundation"
]
```

### Move `mcp_tools_py` to `shim_workspace`

Change from:
```toml
[[modules]]
path = "mcp_coder.mcp_tools_py"
layer = "infrastructure"
```
To:
```toml
[[modules]]
path = "mcp_coder.mcp_tools_py"
layer = "shim_workspace"
```

### Add `mcp_workspace_git` module

```toml
[[modules]]
path = "mcp_coder.mcp_workspace_git"
layer = "shim_workspace"
# Git operations shim. Wraps mcp_workspace.git_operations.
# No internal dependencies — pure re-export.
depends_on = []
```

### Update dependants

The following 7 modules import (directly or transitively) from `mcp_coder.mcp_workspace_git` and each needs `{ path = "mcp_coder.mcp_workspace_git" }` added to their `depends_on` in `tach.toml`:

1. `mcp_coder` (root) — `__init__.py` re-exports git symbols from shim
2. `mcp_coder.cli` — `cli/utils.py` and commands import from shim
3. `mcp_coder.workflows` — multiple workflow modules import from shim
4. `mcp_coder.workflow_utils` — `commit_operations.py`, `base_branch.py`, `failure_handling.py` import from shim
5. `mcp_coder.checks` — `branch_status.py` imports from shim
6. `mcp_coder.utils` — `utils/__init__.py` and `git_utils.py` source from shim
7. `tests` — test files import from shim

Also update the layered architecture contract in `.importlinter`. Both shims (`mcp_coder.mcp_tools_py` and `mcp_coder.mcp_workspace_git`) should be on the **same layer below** `utils`, matching `tach.toml` where both are in `shim_workspace` (below `infrastructure`):
```
mcp_coder.utils
mcp_coder.mcp_tools_py | mcp_coder.mcp_workspace_git
```
This means `utils` can import from either shim, but not vice versa. Both shims are peers.

## ALGORITHM

```
1. Edit .importlinter: remove 2 contracts, add 1 new, update git_library_isolation
2. Edit .importlinter: update layered_architecture to include mcp_workspace_git
3. Edit tach.toml: add shim_workspace layer, move mcp_tools_py, add mcp_workspace_git
4. Edit tach.toml: add mcp_workspace_git dependency to mcp_coder.utils
5. Run lint-imports to verify contracts pass
6. Run tach check to verify boundaries
7. Run pylint, mypy, pytest
8. Commit: "chore: update importlinter and tach for git_operations shim architecture"
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md.

Update .importlinter: remove the git_local and git_operations_internal_layering
contracts. Add the mcp_workspace_git_isolation contract. Update git_library_isolation
to forbid GitPython entirely (no exceptions). Update the layered_architecture contract
to include mcp_workspace_git.

Update tach.toml: add shim_workspace layer, move mcp_tools_py to it, add
mcp_workspace_git module. Update mcp_coder.utils depends_on to include mcp_workspace_git.

Run lint-imports, pylint, mypy, and pytest checks.
Commit with message: "chore: update importlinter and tach for git_operations shim architecture"
```
