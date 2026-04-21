# Step 6 — Delete local `github_operations/` + old tests

> **Reference**: See `pr_info/steps/summary.md` for full context (Issue #833, part 5 of 5).

## Goal

Delete the entire `src/mcp_coder/utils/github_operations/` directory and the corresponding test directory `tests/utils/github_operations/`. At this point, all consumers have been switched to the shim (Step 4) and the standalone function (Step 5).

## WHERE

### Delete entirely:
- `src/mcp_coder/utils/github_operations/` (entire directory tree)
  - `__init__.py`
  - `base_manager.py`
  - `ci_results_manager.py`
  - `github_utils.py`
  - `labels_manager.py`
  - `pr_manager.py`
  - `issues/__init__.py`
  - `issues/base.py`
  - `issues/branch_manager.py`
  - `issues/branch_naming.py`
  - `issues/cache.py`
  - `issues/comments_mixin.py`
  - `issues/events_mixin.py`
  - `issues/labels_mixin.py`
  - `issues/manager.py`
  - `issues/types.py`

- `tests/utils/github_operations/` (entire directory tree)
  - All test files (already covered by mcp_workspace tests)
  - `test_issue_manager_label_update.py` was migrated in Step 3

### Keep (NOT deleted):
- `src/mcp_coder/config/labels.json` — bundled config data
- `src/mcp_coder/config/labels_schema.md` — documentation
- `src/mcp_coder/config/__init__.py` — package init
- `src/mcp_coder/config/label_config.py` — relocated in Step 2

## WHAT

Pure deletion. No code changes — all consumers already point elsewhere.

## HOW

1. Delete `src/mcp_coder/utils/github_operations/` recursively
2. Delete `tests/utils/github_operations/` recursively
3. Verify no imports remain: grep `src/` and `tests/` for `github_operations`
4. Run all checks to confirm nothing is broken

## ALGORITHM

No algorithm — deletion only.

## DATA

No data structure changes.

## Commit

```
refactor: delete local github_operations (now in mcp_workspace)
```

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement step 6 from pr_info/steps/step_6.md.

Delete the entire src/mcp_coder/utils/github_operations/ directory and
tests/utils/github_operations/ directory.
Verify with grep that no imports referencing these deleted modules remain.
Run all checks (pylint, mypy, pytest unit tests) after implementation.
```
