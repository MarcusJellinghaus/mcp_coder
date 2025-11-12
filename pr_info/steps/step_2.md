# Step 2: Update Prompt 3 Timeout References

## LLM Prompt
```
Please review pr_info/steps/summary.md and this step (step_2.md).

Update the two Prompt 3 timeout references in src/mcp_coder/workflows/create_plan.py to use the PROMPT_3_TIMEOUT constant added in Step 1.

Requirements:
1. Update Prompt 3 debug log message (line ~359) - change "timeout=600s" to "timeout={PROMPT_3_TIMEOUT}s"
2. Update Prompt 3 timeout parameter (line ~363) - change "timeout=600," to "timeout=PROMPT_3_TIMEOUT,"
3. Do NOT modify Prompts 1 or 2 (they stay at hardcoded 600)
4. Preserve exact formatting and indentation
5. Ensure f-string formatting is correct in debug log

After implementation:
- Run code quality checks using MCP tools
- Verify both locations updated correctly
- Verify Prompts 1 & 2 still use 600 (unchanged)
```

## Objective
Replace hardcoded 600-second timeout values for Prompt 3 with the `PROMPT_3_TIMEOUT` constant, while keeping Prompts 1 and 2 unchanged.

## Context
- **File**: `src/mcp_coder/workflows/create_plan.py`
- **Function**: `run_planning_prompts()` (starts ~line 220)
- **Principle**: KISS - only modify what's broken (Prompt 3)

## Implementation Details

### WHERE
**File**: `src/mcp_coder/workflows/create_plan.py`
**Function**: `run_planning_prompts()`

**Location 1** - Prompt 3 debug log (~line 359):
```python
logger.debug(
    f"Sending {len(prompt_3)} chars to LLM with session_id={session_id[:16]}... timeout=600s"
)
```

**Location 2** - Prompt 3 execution (~line 363):
```python
response_3 = prompt_llm(
    prompt_3,
    provider=provider,
    method=method,
    session_id=session_id,
    timeout=600,  # <-- This line
    env_vars=env_vars,
    project_dir=str(project_dir),
    mcp_config=mcp_config,
)
```

### WHAT
Update two timeout references for Prompt 3 only.

**Change 1** - Debug log message:
```python
# Before:
logger.debug(
    f"Sending {len(prompt_3)} chars to LLM with session_id={session_id[:16]}... timeout=600s"
)

# After:
logger.debug(
    f"Sending {len(prompt_3)} chars to LLM with session_id={session_id[:16]}... timeout={PROMPT_3_TIMEOUT}s"
)
```

**Change 2** - Function parameter:
```python
# Before:
timeout=600,

# After:
timeout=PROMPT_3_TIMEOUT,
```

### HOW
**Integration**:
- Use the `PROMPT_3_TIMEOUT` constant defined in Step 1
- No new imports needed (constant is in same module)
- Maintain existing code structure and formatting

**What NOT to Change**:
- **Prompt 1 debug log** (~line 285): Keep `timeout=600s`
- **Prompt 1 execution** (~line 287): Keep `timeout=600,`
- **Prompt 2 debug log** (~line 325): Keep `timeout=600s`
- **Prompt 2 execution** (~line 329): Keep `timeout=600,`

### ALGORITHM
Not applicable - this is a simple constant substitution with no logic changes.

### DATA
**No data structure changes**:
- Timeout parameter remains `int` type
- Value changes from 600 to 900 for Prompt 3 only
- Debug log still outputs timeout value in seconds

## Testing Strategy

### Test Approach
Existing tests will validate the changes:

**Relevant Test File**: `tests/workflows/create_plan/test_prompt_execution.py`

The existing tests mock `prompt_llm()` and verify:
- Timeout parameters are passed correctly
- All three prompts execute in sequence
- Error handling works with timeout failures

### Validation Steps
1. **Unit tests**: Verify `prompt_llm()` called with correct timeout values
2. **Code quality**: Run pylint, pytest, mypy via MCP tools
3. **Manual review**: Inspect the two changed lines

### Expected Test Behavior
- Tests should continue passing (no logic changes)
- Mock assertions should validate `timeout=PROMPT_3_TIMEOUT` (900)
- Prompts 1 & 2 should still use timeout=600

## Acceptance Criteria
- [x] Prompt 3 debug log uses `{PROMPT_3_TIMEOUT}s` in f-string
- [x] Prompt 3 execution uses `timeout=PROMPT_3_TIMEOUT,`
- [x] Prompts 1 & 2 remain unchanged (hardcoded 600)
- [x] Debug log correctly displays "timeout=900s" when executed
- [x] All code quality checks pass (pylint, pytest, mypy)
- [x] Existing tests continue to pass

## Code Quality Verification
After implementation, run:
```bash
# Using MCP tools (mandatory per CLAUDE.md)
mcp__code-checker__run_pylint_check(target_directories=["src"])
mcp__code-checker__run_mypy_check(target_directories=["src"])
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"])
```

## Dependencies
- **Depends on**: Step 1 (PROMPT_3_TIMEOUT constant must exist)
- **Required by**: None (final step)

## Line-by-Line Changes

### Change 1: Debug Log (~line 359)
**Before**:
```python
    logger.debug(
        f"Sending {len(prompt_3)} chars to LLM with session_id={session_id[:16]}... timeout=600s"
    )
```

**After**:
```python
    logger.debug(
        f"Sending {len(prompt_3)} chars to LLM with session_id={session_id[:16]}... timeout={PROMPT_3_TIMEOUT}s"
    )
```

**Change**: `timeout=600s` → `timeout={PROMPT_3_TIMEOUT}s`

### Change 2: Timeout Parameter (~line 363)
**Before**:
```python
        response_3 = prompt_llm(
            prompt_3,
            provider=provider,
            method=method,
            session_id=session_id,
            timeout=600,
            env_vars=env_vars,
            project_dir=str(project_dir),
            mcp_config=mcp_config,
        )
```

**After**:
```python
        response_3 = prompt_llm(
            prompt_3,
            provider=provider,
            method=method,
            session_id=session_id,
            timeout=PROMPT_3_TIMEOUT,
            env_vars=env_vars,
            project_dir=str(project_dir),
            mcp_config=mcp_config,
        )
```

**Change**: `timeout=600,` → `timeout=PROMPT_3_TIMEOUT,`

## Notes
- This completes the implementation (final step)
- Total code changes: 1 constant + 2 line modifications
- Extremely low risk - no logic or flow changes
- Follows KISS principle - minimal change for maximum benefit
