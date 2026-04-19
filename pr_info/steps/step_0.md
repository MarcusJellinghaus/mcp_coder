# Step 0: Pre-flight check

> **Read `pr_info/steps/summary.md` first for full context.**

## Goal

Verify that the dependency (issue ②) is complete: `mcp_workspace.git_operations` must exist as a top-level package with the expected submodule structure. If missing, create `pr_info/error.md` and stop.

## WHERE

- Check: `p_workspace` reference project for `mcp_workspace/git_operations/` (top-level, NOT under `file_tools/`)
- Output on failure: `pr_info/error.md`

## WHAT

Verify these exist in `p_workspace`:
- `src/mcp_workspace/git_operations/__init__.py`
- `src/mcp_workspace/git_operations/core.py` (must export `CommitResult`, `_safe_repo_context`)
- `src/mcp_workspace/git_operations/branches.py`
- `src/mcp_workspace/git_operations/branch_queries.py`
- `src/mcp_workspace/git_operations/commits.py`
- `src/mcp_workspace/git_operations/compact_diffs.py`
- `src/mcp_workspace/git_operations/diffs.py`
- `src/mcp_workspace/git_operations/remotes.py`
- `src/mcp_workspace/git_operations/repository_status.py`
- `src/mcp_workspace/git_operations/staging.py`
- `src/mcp_workspace/git_operations/workflows.py` (spot-check: must export `needs_rebase`)
- `src/mcp_workspace/git_operations/parent_branch_detection.py`

## ALGORITHM

```
1. Use list_reference_directory("p_workspace") to check for src/mcp_workspace/git_operations/
2. If NOT found (only file_tools/git_operations exists):
     Create pr_info/error.md describing missing dependency
     STOP — do not proceed to step 1
3. If found: verify key submodules exist by reading __init__.py
4. Proceed to step 1
```

## DATA

`pr_info/error.md` content (on failure):
```markdown
# Pre-flight check failed

## Missing dependency: mcp_workspace.git_operations

Issue ② (MarcusJellinghaus/mcp-workspace#98) has not been completed.
`mcp_workspace.git_operations` does not exist as a top-level package.
Currently only `mcp_workspace.file_tools.git_operations` exists.

This issue cannot proceed until the dependency is resolved.
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_0.md.

Execute the pre-flight check: use the p_workspace reference project to verify
that mcp_workspace.git_operations exists as a top-level package (NOT under
file_tools). If it does not exist, create pr_info/error.md with the error
description and stop. If it exists, confirm readiness to proceed to step 1.
```
