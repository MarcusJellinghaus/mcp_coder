# Issue #374: Show Branch and Base Branch in check branch-status

## Overview

Enhance `mcp-coder check branch-status` to display the current branch name and its base branch in the output, making it easier to understand the branch context at a glance.

## Architectural Changes

### New Module
- **`src/mcp_coder/workflow_utils/base_branch.py`** - Shared utility for base branch detection
  - Extracted from `gh_tool.py` to avoid code duplication
  - Single function `detect_base_branch()` used by `gh_tool.py`, `branch_status.py`, and `implement/core.py`
  - Centralizes detection logic with clear priority: PR → Issue → Default → "unknown"

### Modified Data Structure
- **`BranchStatusReport`** dataclass gains two new fields:
  - `branch_name: str` - Current git branch name
  - `base_branch: str` - Detected parent/base branch

### API Optimization
- Issue data fetched once in `collect_branch_status()` and shared between:
  - Label detection (`_collect_github_label`)
  - Base branch detection (`detect_base_branch`)

## Detection Priority

1. **GitHub PR base branch** - If an open PR exists for current branch
2. **Issue `### Base Branch` section** - Parsed from linked issue body
3. **Default branch** - Repository's main/master branch
4. **"unknown"** - Fallback when all detection fails

## Output Format Changes

### Human-readable format (before title):
```
Branch: 357-feature-branch-name
Base Branch: main

Branch Status Report
...
```

### LLM format (first line):
```
Branch: 357-feature-branch-name | Base: main
Branch Status: CI=PASSED, Rebase=UP_TO_DATE, Tasks=COMPLETE
...
```

## Files to Create

| File | Purpose |
|------|---------|
| `src/mcp_coder/workflow_utils/base_branch.py` | Shared base branch detection function (extracted from gh_tool.py) |
| `tests/workflow_utils/test_base_branch.py` | Unit tests for detection logic (moved from test_gh_tool.py + new tests) |

## Files to Modify

| File | Changes |
|------|---------|
| `src/mcp_coder/workflow_utils/branch_status.py` | Add fields to dataclass, update formatters, share issue data |
| `src/mcp_coder/workflows/implement/core.py` | Refactor `_get_rebase_target_branch()` to use shared function (gains issue-based detection) |
| `src/mcp_coder/cli/commands/gh_tool.py` | Import detection helpers from base_branch.py |
| `tests/workflow_utils/test_branch_status.py` | Update tests for new fields |
| `tests/cli/commands/test_gh_tool.py` | Keep only CLI-specific tests (detection tests moved) |

## Implementation Steps

1. **Step 1**: Extract detection helpers from `gh_tool.py` into `base_branch.py`, create unified `detect_base_branch()` function, move tests
2. **Step 2**: Update `BranchStatusReport` dataclass and `collect_branch_status()` 
3. **Step 3**: Update formatting functions and refactor `implement/core.py`

## Key Decisions

See [Decisions.md](./Decisions.md) for discussion outcomes.

## Acceptance Criteria

- [ ] `detect_base_branch()` function created with correct detection priority
- [ ] `BranchStatusReport` includes `branch_name` and `base_branch` fields
- [ ] Human-readable output shows branch info before title
- [ ] LLM output shows branch info on first line
- [ ] `_get_rebase_target_branch()` refactored to use shared function
- [ ] Issue data fetched once and shared between consumers
- [ ] All unit tests pass
- [ ] CI passes
