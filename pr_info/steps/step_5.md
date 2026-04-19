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

**`jenkins_independence`** — Update `forbidden_modules` to remove `mcp_coder.utils.git_operations` (the module no longer exists). Replace with `mcp_coder.mcp_workspace_git` if jenkins should remain independent from git operations.


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

### Verify with `tach check`

After making changes, run `tach check` to verify that modules importing from `mcp_coder.mcp_workspace_git` (workflows, workflow_utils, checks, cli) don't need explicit `depends_on` entries. If they do, add them.

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

Modules that depend on `mcp_coder.mcp_tools_py` or will depend on `mcp_coder.mcp_workspace_git` may need `depends_on` updates. Check:
- `mcp_coder.utils` — currently depends on `config`, `constants`. After this, `utils/__init__.py` imports from `mcp_workspace_git`, so add `{ path = "mcp_coder.mcp_workspace_git" }` to its depends_on.
- `mcp_coder.workflows` already has `mcp_coder.mcp_tools_py` in depends_on — no change needed since layer hierarchy handles it.

Also update the layered architecture contract in `.importlinter`:
```
mcp_coder.utils | mcp_coder.mcp_tools_py | mcp_coder.mcp_workspace_git
```
Since these are now all at the same conceptual level in the layered architecture contract.

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
