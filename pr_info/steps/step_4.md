# Step 4: Delete local git_operations + cleanup configs

## Context
See [summary.md](summary.md) for full issue context.

After steps 1–3, nothing in `mcp_coder` imports from the local `mcp_coder.utils.git_operations` package. It can now be deleted. Configuration files that referenced it must be cleaned up.

## WHERE

### Files to delete
| File | Description |
|------|-------------|
| `src/mcp_coder/utils/git_operations/__init__.py` | Package init |
| `src/mcp_coder/utils/git_operations/core.py` | Core utilities, `_safe_repo_context` |
| `src/mcp_coder/utils/git_operations/branch_queries.py` | Branch query functions |
| `src/mcp_coder/utils/git_operations/branches.py` | Branch create/delete/checkout |
| `src/mcp_coder/utils/git_operations/commits.py` | Commit operations |
| `src/mcp_coder/utils/git_operations/compact_diffs.py` | Compact diff pipeline |
| `src/mcp_coder/utils/git_operations/diffs.py` | Diff generation |
| `src/mcp_coder/utils/git_operations/file_tracking.py` | File tracking |
| `src/mcp_coder/utils/git_operations/parent_branch_detection.py` | Parent branch detection |
| `src/mcp_coder/utils/git_operations/remotes.py` | Remote operations |
| `src/mcp_coder/utils/git_operations/repository_status.py` | Repository status |
| `src/mcp_coder/utils/git_operations/staging.py` | Staging operations |
| `src/mcp_coder/utils/git_operations/workflows.py` | Workflow orchestration |
| `tests/utils/git_operations/__init__.py` | Test package init |
| `tests/utils/git_operations/test_parent_branch_detection.py` | Parent branch tests |

**Blocker note**: The test file `test_parent_branch_detection.py` contains 4 unique tests not yet in upstream. If MarcusJellinghaus/mcp-workspace#135 has NOT merged, keep the test files and add a TODO comment. If it HAS merged, delete them.

### Files to modify
| File | Action |
|------|--------|
| `.importlinter` | Remove shim exception, remove GitPython exception, update TODO |
| `vulture_whitelist.py` | Remove `PushResult` and `stage_specific_files` entries |

## WHAT

### `.importlinter` changes

#### 1. Remove shim exception from layered_architecture contract
```ini
# REMOVE this line from ignore_imports:
    mcp_coder.mcp_workspace_git -> mcp_coder.utils.git_operations.**
```

#### 2. Update GitPython Library Isolation contract — forbid everywhere
```ini
# BEFORE:
[importlinter:contract:git_library_isolation]
name = GitPython Library Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    git
    gitdb
ignore_imports =
    mcp_coder.utils.git_operations.** -> git

# AFTER:
[importlinter:contract:git_library_isolation]
name = GitPython Library Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    git
    gitdb
```
(Remove the entire `ignore_imports` section — zero exceptions.)

#### 3. Update the TODO comment for MCP Workspace Git Operations Isolation
```ini
# BEFORE:
# TODO(Step 4): Re-add when shim imports from mcp_workspace.git_operations.
# Currently blocked: import-linter v2.11 doesn't support external subpackage
# paths in forbidden_modules, and unmatched ignore_imports cause exit code 1.
# The layered architecture contract enforces shim positioning in the meantime.

# AFTER:
# TODO: Cannot enforce shim-only access to mcp_workspace.git_operations.
# import-linter v2.11 (grimp) doesn't resolve external subpackage paths.
# Enforcement relies on code review + layered architecture contract.
```

### `vulture_whitelist.py` changes

Remove these two entries from the "FALSE POSITIVES - Git Operations" section:
```python
# REMOVE:
_.PushResult
_.stage_specific_files
```

Also remove or update the section comment since the "Dead code to be removed in Step 4" note is now fulfilled.

## ALGORITHM

No logic changes — deletion and config cleanup only.

## DATA

No data structure changes.

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement pr_info/steps/step_4.md.

Delete the local git_operations package and clean up configs:
1. Delete all 13 files in src/mcp_coder/utils/git_operations/
2. Delete tests/utils/git_operations/ (2 files) — if mcp-workspace#135 has
   NOT merged, keep test files and add a TODO comment instead
3. In .importlinter:
   a. Remove `mcp_coder.mcp_workspace_git -> mcp_coder.utils.git_operations.**`
      from layered_architecture ignore_imports
   b. Remove `ignore_imports` entirely from git_library_isolation contract
      (forbid git/gitdb everywhere, zero exceptions)
   c. Update the TODO comment for the git operations isolation section
4. In vulture_whitelist.py: remove PushResult and stage_specific_files entries
5. Run all checks (pylint, mypy, pytest, lint-imports)
```

## Commit message
```
refactor: delete local git_operations and clean up configs (#886)

Remove src/mcp_coder/utils/git_operations/ (13 files) now that
the shim imports from mcp_workspace. Update .importlinter to
forbid GitPython everywhere with zero exceptions. Clean up
vulture whitelist entries.
```
