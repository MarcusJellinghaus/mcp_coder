# MCP Coder Task Tracker

## Overview

This tracks **Feature Implementation** consisting of multiple **Implementation Steps**.

- **Feature**: Fix Architecture Violations and CI Failures
- **Implementation Step**: A self-contained unit of work (tests + implementation)

## Status Legend

- [x] = Implementation step complete
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Implementation Steps

- [ ] [Step 1: Move branch_status.py to Application Layer](steps/step_1.md)
  - Move `branch_status.py` from `utils/` to `workflow_utils/`
  - Update all imports across codebase
  - Move corresponding test file
  - Fixes main import-linter and tach violations

- [ ] [Step 2: Fix Git Operations Internal Layering](steps/step_2.md)
  - Move `needs_rebase` from `branches.py` to `workflows.py`
  - Fixes same-layer import violation within git_operations
  - Update exports in `__init__.py`

- [ ] [Step 3: Fix Vulture Warning](steps/step_3.md)
  - Add `__getattr__` to vulture whitelist
  - Lazy import pattern is a false positive

- [ ] [Step 4: Fix Failing Integration Test](steps/step_4.md)
  - Investigate `test_git_push_force_with_lease_fails_on_unexpected_remote`
  - Determine if test or implementation needs fixing
  - Ensure integration tests pass

---

## Summary

| Step | Description | Status |
|------|-------------|--------|
| 1 | Move branch_status to workflow_utils | Pending |
| 2 | Move needs_rebase to workflows | Pending |
| 3 | Fix vulture whitelist | Pending |
| 4 | Fix integration test | Pending |

## CI Jobs to Fix

| Job | Root Cause | Fixed By |
|-----|------------|----------|
| import-linter | utils → workflow_utils layer violation | Step 1 |
| import-linter | branches → remotes same-layer violation | Step 2 |
| tach | Same as import-linter | Steps 1 & 2 |
| vulture | __getattr__ false positive | Step 3 |
| integration-tests | force-with-lease test failure | Step 4 |
