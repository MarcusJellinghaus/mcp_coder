# Step 1: Reduce Duplicate Protection Threshold

## LLM Prompt

```
Implement Issue #256: Reduce the coordinator duplicate protection threshold from 60 seconds to 50 seconds.

Reference: pr_info/steps/summary.md for context.

This step involves a single line change to reduce the duplicate protection window.
```

## WHERE: File Locations

- **File 1**: `src/mcp_coder/cli/commands/coordinator/workflow_constants.py`
- **File 2**: `src/mcp_coder/cli/commands/coordinator/core.py` (~line 464, inside `get_cached_eligible_issues` function)

## WHAT: Change Description

### workflow_constants.py - Add constant
```python
DUPLICATE_PROTECTION_SECONDS = 50.0
```

### core.py - Import and use constant

**Add import:**
```python
from .workflow_constants import (
    ...
    DUPLICATE_PROTECTION_SECONDS,
)
```

**Before:**
```python
if is_within_duration(last_checked, 60.0, now):
```

**After:**
```python
# 50s: buffer for Jenkins ~60s scheduler variance
if is_within_duration(last_checked, DUPLICATE_PROTECTION_SECONDS, now):
```

## HOW: Integration Points

- New import for `DUPLICATE_PROTECTION_SECONDS` constant
- No interface changes
- Function signature unchanged

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
