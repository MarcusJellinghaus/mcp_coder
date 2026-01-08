# Step 1: Reduce Duplicate Protection Threshold

## LLM Prompt

```
Implement Issue #256: Reduce the coordinator duplicate protection threshold from 60 seconds to 50 seconds.

Reference: pr_info/steps/summary.md for context.

This step involves a single line change to reduce the duplicate protection window.
```

## WHERE: File Location

- **File**: `src/mcp_coder/cli/commands/coordinator/core.py`
- **Line**: ~460 (inside `get_cached_eligible_issues` function)

## WHAT: Change Description

Modify the `is_within_duration` call to use 50.0 seconds instead of 60.0 seconds.

### Before
```python
if is_within_duration(last_checked, 60.0, now):
```

### After
```python
if is_within_duration(last_checked, 50.0, now):
```

## HOW: Integration Points

- No new imports required
- No decorator changes
- No interface changes
- Function signature unchanged

## ALGORITHM

```
1. Locate is_within_duration call in get_cached_eligible_issues function
2. Change first numeric argument from 60.0 to 50.0
3. No other changes needed
```

## DATA: Return Values and Structures

No changes to return values or data structures. The `is_within_duration` function continues to return a boolean.

## TEST VERIFICATION

Existing test `test_get_cached_eligible_issues_duplicate_protection` in `tests/cli/commands/coordinator/test_core.py` uses a 30-second interval:

```python
# Cache checked 30 seconds ago (within 1-minute window)
recent_time = datetime.now().astimezone() - timedelta(seconds=30)
```

This test remains valid because:
- 30 seconds < 50 seconds (new threshold) 
- 30 seconds < 60 seconds (old threshold)
- Test behavior: duplicate protection triggers, no API call made

**No test changes required.**

## ACCEPTANCE CRITERIA

1. ✅ Threshold changed from 60.0 to 50.0
2. ✅ All existing tests pass
3. ✅ Jenkins runs at 50-59 seconds after last check are no longer skipped
