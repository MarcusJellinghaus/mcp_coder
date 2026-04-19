# Step 4: Delete local git_operations package

> **Read `pr_info/steps/summary.md` first for full context.**

## Goal

Delete the entire `src/mcp_coder/utils/git_operations/` directory. At this point all consumers have been switched to the shim (steps 2-3), so these files are unused.

## WHERE

Delete: `src/mcp_coder/utils/git_operations/` (entire directory, 13 files):
- `__init__.py`
- `core.py`
- `branches.py`
- `branch_queries.py`
- `commits.py`
- `compact_diffs.py`
- `diffs.py`
- `file_tracking.py`
- `parent_branch_detection.py`
- `remotes.py`
- `repository_status.py`
- `staging.py`
- `workflows.py`

## WHAT

Clean deletion — no stubs, no re-exports, no deprecation shims in old paths.

## Verification

After deletion, grep the entire `src/` and `tests/` trees to confirm:
- No imports referencing `mcp_coder.utils.git_operations` remain
- No direct `import git` or `from git import` outside the shim

## ALGORITHM

```
1. Delete src/mcp_coder/utils/git_operations/ directory
2. Grep verify: no remaining references to mcp_coder.utils.git_operations
3. Grep verify: no direct GitPython imports in mcp_coder (except shim)
4. Run pytest (unit tests only)
5. Run pylint, mypy
6. Commit: "refactor: delete local git_operations package (now consumed via shim)"
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Delete the entire src/mcp_coder/utils/git_operations/ directory (all 13 files).
Verify with grep that no imports referencing mcp_coder.utils.git_operations remain
anywhere in src/ or tests/. Also verify no direct GitPython (import git) imports
exist outside the shim. Run pylint, mypy, and pytest checks.
Commit with message: "refactor: delete local git_operations package (now consumed via shim)"
```
