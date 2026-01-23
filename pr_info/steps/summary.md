# Issue #327: Do Not Log Tokens in Return Values

## Summary

Sensitive tokens (e.g., GitHub tokens) are logged in plaintext when `get_config_values()` returns dictionaries with **tuple keys** like `('github', 'token')`. The `_redact_for_logging()` function only checks if dictionary keys match sensitive field names as strings, but tuple keys don't match.

## Root Cause

```python
# Current code in _redact_for_logging():
if key in sensitive_fields:  # key is ('github', 'token'), not 'token'
```

The tuple `('github', 'token')` doesn't match the string `'token'`, so redaction is skipped.

## Solution

Modify `_redact_for_logging()` to extract the last element from tuple keys before checking against sensitive fields.

---

## Architectural / Design Changes

### Change Type: Bug Fix (Minor Enhancement)

**No architectural changes required.** This is a targeted fix to an existing function.

### Design Decision

- **Approach**: When a dictionary key is a tuple, check if its **last element** matches a sensitive field name
- **Rationale**: The tuple format `('section', 'key')` always has the actual field name as the last element
- **Backward Compatibility**: Existing string-key behavior remains unchanged

### Code Change

```python
# Before (line ~243 in log_utils.py):
for key in result:
    if key in sensitive_fields:
        result[key] = REDACTED_VALUE

# After:
for key in result:
    match_key = key[-1] if isinstance(key, tuple) and key else key
    if match_key in sensitive_fields:
        result[key] = REDACTED_VALUE
```

**Lines changed**: 2 lines modified in `_redact_for_logging()`

---

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/utils/log_utils.py` | MODIFY | Update `_redact_for_logging()` to handle tuple keys |
| `tests/utils/test_log_utils.py` | MODIFY | Add tests for tuple-key redaction in `TestRedactForLogging` class |

## Files NOT Changed

- `src/mcp_coder/utils/user_config.py` - No changes needed (already has correct `sensitive_fields` config)
- No new files created

---

## Acceptance Criteria Mapping

| Criteria | How Verified |
|----------|--------------|
| `_redact_for_logging()` redacts values when last element of tuple key matches | Unit test: `test_redact_tuple_key_matches_last_element` |
| Existing string-key redaction continues to work | Existing tests remain passing |
| Nested dictionary redaction continues to work | Existing test: `test_redact_nested_dict` |
| Log output shows `{('github', 'token'): '***'}` | Unit test verifies redacted output |
| Tests added for tuple-key redaction | New test class: `TestRedactForLoggingTupleKeys` |

---

## Implementation Steps

1. **Step 1**: Add unit tests for tuple-key redaction (TDD)
2. **Step 2**: Implement the fix in `_redact_for_logging()`

---

## Risk Assessment

- **Risk**: Low - Minimal code change, isolated to one function
- **Testing**: Comprehensive unit tests cover all scenarios
- **Rollback**: Simple revert if issues arise
