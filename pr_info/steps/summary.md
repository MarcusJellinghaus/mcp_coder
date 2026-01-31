# Implementation Summary: PR Info Lifecycle Management

## Overview

This implementation improves the `pr_info/` folder lifecycle management across three workflows:
- **Plan Creation**: Fail if `pr_info/` exists, create folder structure
- **Implement Workflow**: Auto-create task tracker from template, validate structure
- **PR Creation**: Delete entire `pr_info/` folder (simplified cleanup)

## Architectural Changes

### Design Principle: Centralized Lifecycle Management

```
┌─────────────────┐
│  Plan Creation  │ → Fail if pr_info/ exists
│                 │ → Create pr_info/, steps/, .conversations/
└────────┬────────┘
         ▼
┌─────────────────┐
│ check_prereqs   │ → Create TASK_TRACKER.md from template if missing
│ (implement)     │ → Validate structure if exists
└────────┬────────┘
         ▼
┌─────────────────┐
│   Create PR     │ → Delete entire pr_info/ folder
│                 │ → Single cleanup function replaces 3 partial ones
└─────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Template in `task_tracker.py` | Co-locate with parsing logic, single source of truth |
| Wrap `_find_implementation_section()` | Reuse existing validation, no code duplication |
| Single `delete_pr_info_directory()` | Simpler than 3 partial delete functions |
| Fail if `pr_info/` exists | Explicit cleanup required, prevents stale state |

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/workflow_utils/task_tracker.py` | ADD | `TASK_TRACKER_TEMPLATE` constant, `validate_task_tracker()` function |
| `src/mcp_coder/workflows/implement/prerequisites.py` | MODIFY | Template creation + validation in `check_prerequisites()` |
| `src/mcp_coder/workflows/create_pr/core.py` | MODIFY | Add `delete_pr_info_directory()`, simplify `cleanup_repository()`, remove 3 functions |
| `src/mcp_coder/workflows/create_plan.py` | MODIFY | Add existence check + directory creation, remove `verify_steps_directory()` |

## Test Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `tests/workflow_utils/test_task_tracker.py` | ADD | Tests for `validate_task_tracker()` and template constant |
| `tests/workflows/implement/test_prerequisites.py` | ADD | Tests for template creation and validation |
| `tests/workflows/create_pr/test_file_operations.py` | MODIFY | Tests for `delete_pr_info_directory()`, remove tests for deleted functions |
| `tests/workflows/create_plan/test_prerequisites.py` | MODIFY | Tests for existence check and directory creation |

## Net Code Impact

- **Removed**: 3 functions from `create_pr/core.py`, 1 function from `create_plan.py`
- **Added**: 1 constant + 1 function in `task_tracker.py`, 1 function in `create_pr/core.py`
- **Result**: Simpler, more maintainable code with clearer lifecycle semantics

## Implementation Steps

1. **Step 1**: Add template and validation to `task_tracker.py` (with tests)
2. **Step 2**: Update `prerequisites.py` for template creation + validation (with tests)
3. **Step 3**: Simplify `create_pr/core.py` cleanup (with tests)
4. **Step 4**: Update `create_plan.py` for existence check + directory creation (with tests)
