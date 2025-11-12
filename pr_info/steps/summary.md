# Summary: Increase Timeout for Implementation Plan Creation Prompt

## Overview
Increase the timeout for the third planning prompt ("Implementation Plan Creation") from 10 minutes (600s) to 15 minutes (900s) to prevent timeout failures when processing complex GitHub issues that require detailed multi-file implementation plans.

## Problem Statement
The `create_plan` workflow times out during the "Implementation Plan Creation" prompt (prompt 3 of 3) when generating detailed implementation plans. This prompt generates comprehensive plans with multiple files, pseudocode, algorithms, and file structures - requiring more time than the current 10-minute timeout allows.

## Root Cause
All three sequential planning prompts use a hardcoded 600-second timeout:
1. **Prompt 1** - Initial Analysis (600s is adequate)
2. **Prompt 2** - Simplification Review (600s is adequate)  
3. **Prompt 3** - Implementation Plan Creation (600s is **insufficient**)

## Solution (KISS Approach)
Following the KISS principle, we implement a **minimal, targeted fix**:

- Add **ONE** timeout constant for Prompt 3: `PROMPT_3_TIMEOUT = 900` (15 minutes)
- Keep Prompts 1 & 2 unchanged at 600s (hardcoded - they work fine)
- Update only **2 locations** in the code (both for Prompt 3)

### Why KISS?
- **Minimal change**: Only fix what's broken (Prompt 3)
- **Clear intent**: Single constant signals "this prompt is special"
- **Easy maintenance**: One value to understand vs three
- **Self-documenting**: Existence of PROMPT_3_TIMEOUT clearly indicates special handling needed

## Architectural / Design Changes

### No Architectural Changes
This is a **configuration adjustment**, not an architectural change:
- No new modules, classes, or functions
- No changes to data flow or system boundaries
- No new dependencies or external integrations
- Workflow sequence remains unchanged (3 sequential prompts)

### Design Changes (Minimal)
- **Addition**: One module-level constant `PROMPT_3_TIMEOUT = 900`
- **Modification**: Two timeout references in `run_planning_prompts()` function
- **Principle**: Special-case handling for high-complexity prompt

### Design Rationale
- **Not configurable**: Timeout is implementation detail, not user configuration
- **Not all prompts**: Only Prompt 3 needs special handling (YAGNI principle)
- **Future-proof**: If other prompts need adjustment later, add constants then

## Files to Modify

### Modified Files (1 file)
```
src/mcp_coder/workflows/create_plan.py
  - Add: PROMPT_3_TIMEOUT constant (after logger setup, before functions)
  - Modify: Line ~359 - Prompt 3 debug log message
  - Modify: Line ~363 - Prompt 3 timeout parameter
```

### No New Files Created
This is a configuration change to an existing workflow module.

## Test Strategy

### Existing Tests (No Changes Required)
The existing test suite validates the fix:
- `tests/workflows/create_plan/test_prompt_execution.py` - Tests prompt execution with various timeout scenarios
- Tests already mock `prompt_llm()` calls and verify timeout parameters
- No new test files needed - existing tests will validate correct timeout values

### Validation Approach
1. **Unit tests**: Existing tests verify timeout parameter passed correctly
2. **Code quality**: All three checks (pylint, pytest, mypy) must pass
3. **Manual verification**: Review constant value and updated locations

## Benefits
- ✅ Prevents timeout failures for complex implementation plans
- ✅ Maintains reasonable timeouts for simpler prompts (no unnecessary waiting)
- ✅ Clear, self-documenting code with explanatory comments
- ✅ Easy to adjust Prompt 3 timeout independently if needed
- ✅ Minimal code change with no behavioral changes except timeout duration

## Acceptance Criteria
- [x] `PROMPT_3_TIMEOUT = 900` constant defined with clear comment
- [x] Prompt 1 continues using 600-second timeout (hardcoded)
- [x] Prompt 2 continues using 600-second timeout (hardcoded)
- [x] Prompt 3 uses 900-second timeout (via constant)
- [x] Debug log messages reflect correct timeout values
- [x] All code quality checks pass (pylint, pytest, mypy)
- [x] Existing tests continue to pass
- [x] Timeout error handling continues to work correctly

## Scope
**In Scope:**
- Add PROMPT_3_TIMEOUT constant
- Update Prompt 3 timeout references (2 locations)
- Verify code quality checks pass

**Out of Scope:**
- Configuration file support (timeout is implementation detail)
- Changing timeouts for Prompts 1 or 2 (working fine)
- Adding timeout constants for all prompts (YAGNI)
- Modifying prompt content or workflow sequence
- Changing error handling or retry logic

## Implementation Complexity
**Complexity**: Very Low (⭐☆☆☆☆)
- Single constant addition
- Two line modifications
- No logic changes
- No test changes required

**Estimated Effort**: 15-30 minutes
- Implementation: 5 minutes
- Code quality checks: 10 minutes
- Verification: 5 minutes
