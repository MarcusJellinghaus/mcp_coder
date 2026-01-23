# Step 2: Implement Tuple-Key Redaction Fix

## LLM Prompt

```
You are implementing Issue #327: Do Not Log Tokens in Return Values.

Read the summary at `pr_info/steps/summary.md` for context.
Read Step 1 at `pr_info/steps/step_1.md` to see the tests that were added.

This is Step 2: Implement the fix in _redact_for_logging().

The tests from Step 1 should now PASS after this implementation.
```

---

## WHERE

**File to modify**: `src/mcp_coder/utils/log_utils.py`

**Function**: `_redact_for_logging()` (around line 242-258)

---

## WHAT

### Function Signature (unchanged)

```python
def _redact_for_logging(
    data: dict[str, Any],
    sensitive_fields: set[str],
) -> dict[str, Any]:
```

Note: The type hint `dict[str, Any]` is slightly inaccurate (keys can be tuples), but changing it would be a larger refactor. The function works correctly with `Any` keys.

---

## HOW

### Current Code (lines ~250-258)

```python
def _redact_for_logging(
    data: dict[str, Any],
    sensitive_fields: set[str],
) -> dict[str, Any]:
    """Create a copy of data with sensitive fields redacted for logging."""
    result = data.copy()
    for key in result:
        if key in sensitive_fields:
            result[key] = REDACTED_VALUE
        elif isinstance(result[key], dict):
            result[key] = _redact_for_logging(result[key], sensitive_fields)
    return result
```

### Modified Code

```python
def _redact_for_logging(
    data: dict[str, Any],
    sensitive_fields: set[str],
) -> dict[str, Any]:
    """Create a copy of data with sensitive fields redacted for logging."""
    result = data.copy()
    for key in result:
        # For tuple keys like ('github', 'token'), check last element
        match_key = key[-1] if isinstance(key, tuple) and key else key
        if match_key in sensitive_fields:
            result[key] = REDACTED_VALUE
        elif isinstance(result[key], dict):
            result[key] = _redact_for_logging(result[key], sensitive_fields)
    return result
```

---

## ALGORITHM

```
FOR each key in dictionary:
    IF key is a non-empty tuple:
        match_key = last element of tuple (key[-1])
    ELSE:
        match_key = key itself
    
    IF match_key in sensitive_fields:
        redact the value
    ELSE IF value is a dict:
        recursively redact
```

---

## DATA

### Before/After Examples

| Input | Before (Bug) | After (Fixed) |
|-------|--------------|---------------|
| `{('github', 'token'): 'ghp_xxx'}` | `{('github', 'token'): 'ghp_xxx'}` | `{('github', 'token'): '***'}` |
| `{'token': 'xxx'}` | `{'token': '***'}` | `{'token': '***'}` (unchanged) |
| `{('a', 'b', 'token'): 'xxx'}` | `{('a', 'b', 'token'): 'xxx'}` | `{('a', 'b', 'token'): '***'}` |

---

## VERIFICATION

After implementing the fix, run:

```bash
# Run the new tuple-key tests
pytest tests/utils/test_log_utils.py::TestRedactForLoggingTupleKeys -v

# Run all log_utils tests to ensure no regressions
pytest tests/utils/test_log_utils.py -v

# Run the full test suite
pytest tests/ -v
```

**Expected**: All tests should PASS (green phase of TDD).

---

## CHANGE SUMMARY

| Line | Change |
|------|--------|
| ~252 | Add: `match_key = key[-1] if isinstance(key, tuple) and key else key` |
| ~253 | Modify: `if key in sensitive_fields:` → `if match_key in sensitive_fields:` |

**Total**: 2 lines changed
