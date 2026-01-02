# Summary: Support for Multi-Phase Task Tracker (#156)

## Overview

This implementation adds support for multi-phase task trackers in the `workflow_utils/task_tracker.py` module. Currently, the parser stops when it encounters phase headers (e.g., `## Phase 2:`), causing incomplete tasks in subsequent phases to be missed.

## Problem Statement

The current `_find_implementation_section()` function treats same-level headers as section boundaries. When a task tracker uses phases:

```markdown
## Tasks

## Phase 1: Initial Implementation ✅ COMPLETE
### Step 1: ...
- [x] Completed task

## Phase 2: Code Review Fixes 📋 NEW  
### Step 6: ...
- [ ] Incomplete task  ← THIS IS MISSED!
```

The parser stops at `## Phase 2:` because it's at the same level (`##`) as `## Tasks`, missing all Phase 2 tasks.

## Solution

Simplify the parsing logic to use **boundary-based extraction**:
1. Find the `## Tasks` header as the start boundary
2. Find the `## Pull Request` header as the end boundary (if present)
3. Extract everything between these boundaries
4. If no end boundary, extract everything after `## Tasks`

This approach is simpler and more robust than tracking header levels or keywords.

## Architectural / Design Changes

### Modified Components

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/workflow_utils/task_tracker.py` | **Modified** | Update `_find_implementation_section()` to handle phase headers |
| `tests/workflow_utils/test_task_tracker.py` | **Modified** | Add test cases for multi-phase parsing (inline test data) |

### No New Modules Required

This is a targeted fix within the existing `task_tracker.py` module. No new classes, modules, or architectural patterns are introduced.

### Design Decisions

1. **Pattern Recognition**: Use keyword matching ("phase") to identify phase headers as continuations
2. **Explicit Stop Markers**: Only stop at "pull request" section (case-insensitive)
3. **Backward Compatibility**: All existing tests must continue to pass

## Algorithm Change

**Current Logic** (problematic):
```
1. Find "## Tasks" or "### Implementation Steps" → start collecting
2. Track header levels
3. Stop at same-level or higher-level headers
4. Stop at "Pull Request"
```
Problem: `## Phase 2:` is same level as `## Tasks`, so parsing stops too early.

**New Logic** (boundary-based):
```
1. Find "## Tasks" or "### Implementation Steps" → mark start line
2. Find "## Pull Request" → mark end line (or use end of file)
3. Extract everything between start and end
4. Log debug info: headers, line numbers, line count
```
Simpler: No header level tracking, no keyword detection—just find boundaries and extract.

## Files to Create/Modify

### Files to Modify
- `src/mcp_coder/workflow_utils/task_tracker.py` - Core parsing logic
- `tests/workflow_utils/test_task_tracker.py` - Test cases

### Files to Create
- `pr_info/steps/step_1.md` - Implementation step 1
- `pr_info/steps/step_2.md` - Implementation step 2
- `pr_info/steps/step_3.md` - Implementation step 3
- `pr_info/steps/Decisions.md` - Decisions log from plan review

## Implementation Steps Overview

| Step | Description | Effort |
|------|-------------|--------|
| 1 | Add unit tests for multi-phase parsing (TDD) with inline test data | ~30 min |
| 2 | Add logging and update `_find_implementation_section()` | ~20 min |
| 3 | Run quality checks and verify backward compatibility | ~15 min |
| 4 | Revert incorrect type ignore comments on requests imports | ~10 min |

**Total Estimated Time**: ~1 hour 15 min

## Key Decisions (see Decisions.md for details)

- **Decision 3**: Use boundary-based extraction (find content between `## Tasks` and `## Pull Request`)
- **Decision 12**: Remove Step 4 — keep all 5 tests, no cleanup step needed
- **Decision 14**: Use inline test data (no separate test data file)
- **Decision 16**: Revert incorrect type ignore comments (types-requests already in dev deps)

## Success Criteria

1. ✅ All existing tests pass (backward compatibility)
2. ✅ New tests for multi-phase trackers pass
3. ✅ `get_incomplete_tasks()` returns tasks from all phases
4. ✅ `get_step_progress()` includes steps from all phases
5. ✅ pylint, pytest, mypy checks pass

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking existing trackers | Low | Extensive existing test suite + new tests |
| Edge cases in header parsing | Medium | Test with real-world examples from issue |
| Performance regression | Very Low | No algorithmic complexity change |
