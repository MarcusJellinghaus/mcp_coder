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

Modify the parsing logic to:
1. Recognize "phase" headers as **continuations** within the Tasks section
2. Only stop parsing at explicit end markers ("Pull Request") or truly unrelated sections
3. Maintain backward compatibility with single-phase trackers

## Architectural / Design Changes

### Modified Components

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/workflow_utils/task_tracker.py` | **Modified** | Update `_find_implementation_section()` to handle phase headers |
| `tests/workflow_utils/test_task_tracker.py` | **Modified** | Add test cases for multi-phase parsing |
| `tests/workflow_utils/test_data/multi_phase_tracker.md` | **New** | Test data file with multi-phase structure |

### No New Modules Required

This is a targeted fix within the existing `task_tracker.py` module. No new classes, modules, or architectural patterns are introduced.

### Design Decisions

1. **Pattern Recognition**: Use keyword matching ("phase") to identify phase headers as continuations
2. **Explicit Stop Markers**: Only stop at "pull request" section (case-insensitive)
3. **Backward Compatibility**: All existing tests must continue to pass

## Algorithm Change

**Current Logic** (problematic):
```
if header_level <= impl_section_level:
    break  # Stops at Phase 2!
```

**New Logic** (fixed):
```
if header_level <= impl_section_level:
    if "phase" in header_text:
        continue  # Phase headers are continuations
    elif "pull request" in header_text:
        break  # Explicit end marker
    else:
        break  # Other same-level headers end section
```

## Files to Create/Modify

### Files to Modify
- `src/mcp_coder/workflow_utils/task_tracker.py` - Core parsing logic
- `tests/workflow_utils/test_task_tracker.py` - Test cases

### Files to Create
- `tests/workflow_utils/test_data/multi_phase_tracker.md` - Test data
- `pr_info/steps/step_1.md` - Implementation step 1
- `pr_info/steps/step_2.md` - Implementation step 2
- `pr_info/steps/step_3.md` - Implementation step 3

## Implementation Steps Overview

| Step | Description | Effort |
|------|-------------|--------|
| 1 | Create test data and add unit tests for multi-phase parsing (TDD) | ~30 min |
| 2 | Update `_find_implementation_section()` to handle phase headers | ~20 min |
| 3 | Run quality checks and verify backward compatibility | ~15 min |

**Total Estimated Time**: ~1 hour

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
