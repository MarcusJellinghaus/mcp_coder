# Step 5: Update Tests and Final Verification

## LLM Prompt

```
Implement Step 5 of Issue #228 (see pr_info/steps/summary.md for context).

Update all test files that reference the old `get_config_value()` function and 
perform final verification that all acceptance criteria are met.

Requirements:
- Update test_user_config.py tests for new batch API
- Update test_user_config_integration.py tests for new batch API  
- Run full test suite to verify all tests pass
- Verify no references to old function remain
```

## WHERE: File Paths

- `tests/utils/test_user_config.py` - Unit tests
- `tests/utils/test_user_config_integration.py` - Integration tests

## WHAT: Test Updates Required

### Pattern: Converting get_config_value Tests to get_config_values

**Before:**
```python
def test_get_config_value_success_string(self):
    result = get_config_value("tokens", "github")
    assert result == "ghp_test_token_123"
```

**After:**
```python
def test_get_config_values_success_string(self):
    result = get_config_values([("tokens", "github", None)])
    assert result[("tokens", "github")] == "ghp_test_token_123"
```

---

## Test File Updates

### `test_user_config.py` - TestGetConfigValue Class

Rename class to `TestGetConfigValues` and update all methods:

| Old Test | New Test |
|----------|----------|
| `test_get_config_value_success_string` | `test_get_config_values_success_string` |
| `test_get_config_value_success_non_string` | `test_get_config_values_success_non_string` |
| `test_get_config_value_success_boolean` | `test_get_config_values_success_boolean` |
| `test_get_config_value_missing_file` | `test_get_config_values_missing_file` |
| `test_get_config_value_missing_section` | `test_get_config_values_missing_section` |
| `test_get_config_value_missing_key` | `test_get_config_values_missing_key` |
| `test_get_config_value_invalid_toml_raises` | `test_get_config_values_invalid_toml_raises` |
| `test_get_config_value_io_error_raises` | `test_get_config_values_io_error_raises` |
| `test_get_config_value_null_value` | `test_get_config_values_empty_value` |
| `test_get_config_value_nested_section_success` | `test_get_config_values_nested_section_success` |
| `test_get_config_value_nested_section_different_repo` | `test_get_config_values_nested_section_different_repo` |
| `test_get_config_value_nested_section_missing_intermediate` | `test_get_config_values_nested_section_missing_intermediate` |
| `test_get_config_value_nested_section_missing_leaf` | `test_get_config_values_nested_section_missing_leaf` |
| `test_get_config_value_nested_section_missing_key` | `test_get_config_values_nested_section_missing_key` |

### Update Import Statement
```python
# Before
from mcp_coder.utils.user_config import get_config_value

# After  
from mcp_coder.utils.user_config import get_config_values
```

---

### `test_user_config_integration.py` Updates

Same pattern - update all references from `get_config_value` to `get_config_values`:

```python
# Before
assert get_config_value("tokens", "github") == "ghp_real_integration_token"

# After
result = get_config_values([("tokens", "github", None)])
assert result[("tokens", "github")] == "ghp_real_integration_token"
```

---

## Final Verification Checklist

### Code Verification
```bash
# Search for any remaining references to old function
grep -r "get_config_value" src/ tests/ --include="*.py" | grep -v "get_config_values"
```

Expected: No results (all references should be to `get_config_values`)

### Run Full Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run with coverage to verify nothing missed
pytest tests/ --cov=mcp_coder --cov-report=term-missing
```

### Manual Log Verification

Create a simple test script to verify log output:
```python
import logging
from mcp_coder.utils.log_utils import setup_logging
from mcp_coder.utils.user_config import load_config

setup_logging("DEBUG")
config = load_config()
# Check console output shows:
# 1. Logger name is "mcp_coder.utils.user_config" NOT "mcp_coder.utils.log_utils"
# 2. Token values show as "***" NOT actual values
```

---

## Acceptance Criteria Verification

| Criteria | How to Verify |
|----------|---------------|
| `@log_function_call` accepts `sensitive_fields` | Unit tests in test_log_utils.py |
| Sensitive params display as `***` | Unit tests + manual log check |
| Sensitive return keys display as `***` | Unit tests + manual log check |
| Logger name reflects decorated function's module | Unit tests + manual log check |
| `get_config_value()` removed | grep search returns no results |
| `get_config_values()` works | Unit tests + integration tests |
| All 8 callers refactored | Code review + grep verification |
| Minimal log entries per batch | Manual log check (1 entry per batch) |
| All existing tests pass | pytest runs green |

---

## Implementation Checklist

- [ ] Update `test_user_config.py` - rename class, update all test methods
- [ ] Update `test_user_config_integration.py` - update all references
- [ ] Update imports in both test files
- [ ] Run grep to verify no old references remain
- [ ] Run full test suite
- [ ] Manual verification of log output format
- [ ] Verify all acceptance criteria met
