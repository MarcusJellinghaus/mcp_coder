# Issue #196: Fix Windows Template Selection in Coordinator Run Command

## Problem Statement

The `coordinator run` command always generates Linux shell commands even when `executor_os="windows"` is configured. This causes Jenkins jobs to fail on Windows agents.

## Root Cause

In `execute_coordinator_run()`, the `validated_config` dict passed to `dispatch_workflow()` does not include the `executor_os` field. As a result, `dispatch_workflow()` defaults to `"linux"`.

## Solution Overview

Add the missing `executor_os` field to `validated_config` in `execute_coordinator_run()`.

## Architectural / Design Changes

**None.** This is a bug fix, not an architectural change. The design is correct:
- `load_repo_config()` correctly loads and normalizes `executor_os`
- `dispatch_workflow()` correctly selects templates based on `executor_os`
- The bug is simply a missing field in a dictionary

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/cli/commands/coordinator.py` | Modify | Add `executor_os` to `validated_config` dict |
| `tests/cli/commands/test_coordinator.py` | Modify | Add regression test for `executor_os` passthrough |

## Implementation Steps

1. **Step 1**: Add test coverage for `executor_os` passthrough in `execute_coordinator_run()`
2. **Step 2**: Fix the bug by adding `executor_os` to `validated_config`

## Success Criteria

- When `executor_os="windows"` is configured, Windows batch templates are used
- When `executor_os="linux"` (or not specified), Linux shell templates are used
- All existing tests continue to pass
- New regression test prevents future regressions
