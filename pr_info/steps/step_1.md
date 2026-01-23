# Step 1: Add Unit Tests for Tuple-Key Redaction (TDD)

## LLM Prompt

```
You are implementing Issue #327: Do Not Log Tokens in Return Values.

Read the summary at `pr_info/steps/summary.md` for context.

This is Step 1: Add unit tests for tuple-key redaction following TDD principles.

Add tests BEFORE implementing the fix. The tests should initially FAIL.
```

---

## WHERE

**File to modify**: `tests/utils/test_log_utils.py`

**Location**: Add new test class `TestRedactForLoggingTupleKeys` after the existing `TestRedactForLogging` class (around line 340)

---

## WHAT

### New Test Class: `TestRedactForLoggingTupleKeys`

Add 4 focused test methods:

```python
def test_redact_tuple_key_matches_last_element(self) -> None:
    """Test that tuple keys are redacted when last element matches sensitive field."""

def test_redact_mixed_string_and_tuple_keys(self) -> None:
    """Test redaction works with both string and tuple keys in same dict."""

def test_redact_tuple_key_no_match(self) -> None:
    """Test that tuple keys not matching sensitive fields are unchanged."""

def test_redact_empty_tuple_key_unchanged(self) -> None:
    """Test that empty tuple keys are handled safely (no crash, no match)."""
```

---

## HOW

### Integration Points

- Import: `from mcp_coder.utils.log_utils import _redact_for_logging` (already imported)
- Test class follows existing pattern in file
- Uses pytest (no additional fixtures needed)

---

## ALGORITHM

```
Test 1 (tuple key matches):
    data = {('github', 'token'): 'secret', ('user', 'name'): 'john'}
    result = _redact_for_logging(data, {'token'})
    assert result[('github', 'token')] == '***'
    assert result[('user', 'name')] == 'john'

Test 2 (mixed keys):
    data = {'token': 'secret1', ('github', 'token'): 'secret2', 'name': 'test'}
    result = _redact_for_logging(data, {'token'})
    assert both tokens == '***'
    assert 'name' unchanged

Test 3 (no match):
    data = {('github', 'username'): 'user'}
    result = _redact_for_logging(data, {'token'})
    assert value unchanged
```

---

## DATA

### Test Input/Output Examples

| Input | Sensitive Fields | Expected Output |
|-------|------------------|-----------------|
| `{('github', 'token'): 'ghp_xxx'}` | `{'token'}` | `{('github', 'token'): '***'}` |
| `{('jenkins', 'api_token'): 'xxx', ('jenkins', 'url'): 'http://...'}` | `{'api_token'}` | `{('jenkins', 'api_token'): '***', ('jenkins', 'url'): 'http://...'}` |
| `{'token': 'a', ('x', 'token'): 'b'}` | `{'token'}` | `{'token': '***', ('x', 'token'): '***'}` |

---

## VERIFICATION

After adding tests, run using MCP tool:
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "tests/utils/test_log_utils.py::TestRedactForLoggingTupleKeys", "-v"]
)
```

**Expected**: Tests should FAIL (red phase of TDD) because the fix is not yet implemented.

---

## CODE TO ADD

Add the following after `TestRedactForLogging` class (around line 340):

```python
class TestRedactForLoggingTupleKeys:
    """Tests for _redact_for_logging with tuple dictionary keys.
    
    Issue #327: get_config_values() returns dicts with tuple keys like
    ('github', 'token'). The redaction should check the last element
    of tuple keys against sensitive_fields.
    """

    def test_redact_tuple_key_matches_last_element(self) -> None:
        """Test that tuple keys are redacted when last element matches sensitive field."""
        data = {
            ("github", "token"): "ghp_secret123",
            ("user", "name"): "john",
        }
        result = _redact_for_logging(data, {"token"})

        assert result[("github", "token")] == "***"
        assert result[("user", "name")] == "john"
        # Original unchanged
        assert data[("github", "token")] == "ghp_secret123"

    def test_redact_mixed_string_and_tuple_keys(self) -> None:
        """Test redaction works with both string and tuple keys in same dict."""
        data = {
            "token": "direct_secret",
            ("github", "token"): "tuple_secret",
            "username": "user",
        }
        result = _redact_for_logging(data, {"token"})

        assert result["token"] == "***"
        assert result[("github", "token")] == "***"
        assert result["username"] == "user"

    def test_redact_tuple_key_no_match(self) -> None:
        """Test that tuple keys not matching sensitive fields are unchanged."""
        data = {
            ("github", "username"): "user",
            ("jenkins", "url"): "http://example.com",
        }
        result = _redact_for_logging(data, {"token", "api_token"})

        assert result[("github", "username")] == "user"
        assert result[("jenkins", "url")] == "http://example.com"

    def test_redact_empty_tuple_key_unchanged(self) -> None:
        """Test that empty tuple keys are handled safely (no crash, no match)."""
        data = {
            (): "empty_tuple_value",
            ("normal", "key"): "normal_value",
        }
        result = _redact_for_logging(data, {"token"})

        # Empty tuple should not crash and value should be unchanged
        assert result[()] == "empty_tuple_value"
        assert result[("normal", "key")] == "normal_value"
```
