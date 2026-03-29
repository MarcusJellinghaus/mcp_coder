# Step 1: Clean HTTP error messages in `start_job()`

> **Reference**: See `pr_info/steps/summary.md` for full context on issue #626.

## Goal

When `start_job()` catches an `HTTPError`, produce a clean one-liner instead of dumping the full URL-encoded request. Keep non-HTTP errors unchanged.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/utils/jenkins_operations/client.py` | Add helper + modify except block |
| `tests/utils/jenkins_operations/test_client.py` | Add test class `TestStartJobHttpErrorMessages` |

## WHAT

### New helper function in `client.py`

```python
def _http_error_hint(status_code: int) -> str:
```

- **Signature**: `(status_code: int) -> str`
- **Returns**: Human-readable hint string (with leading space+parens) or empty string
- **Location**: Module-level, before `JenkinsClient` class

### Modified: `JenkinsClient.start_job()` except block

Update the existing except block (lines ~133-142) to detect `HTTPError` and format cleanly.

## HOW

### Import added to `client.py`

```python
from requests.exceptions import HTTPError
```

### Integration

No new decorators, no new classes, no changes to method signatures. Just the except block logic changes.

## ALGORITHM (pseudocode)

```
except Exception as e:
    if isinstance(e, HTTPError) and e.response is not None:
        code = e.response.status_code
        reason = e.response.reason
        hint = _http_error_hint(code)
        msg = f"Failed to start job '{job_path}': {code} {reason}{hint}"
    else:
        msg = f"Failed to start job '{job_path}': {str(e)}"
    raise JenkinsError(msg) from e
```

```
def _http_error_hint(status_code):
    hints = {409: " (job may be disabled, already queued, or running)"}
    return hints.get(status_code, "")
```

## DATA

### `_http_error_hint` return values

| Input | Output |
|-------|--------|
| `409` | `" (job may be disabled, already queued, or running)"` |
| `500` | `""` |
| `404` | `""` |

### Error message examples

| Scenario | Message |
|----------|---------|
| HTTP 409 | `"Failed to start job 'Windows-Agents/Executor': 409 Conflict (job may be disabled, already queued, or running)"` |
| HTTP 500 | `"Failed to start job 'Windows-Agents/Executor': 500 Internal Server Error"` |
| Non-HTTP | `"Failed to start job 'test-job': Job not found"` (unchanged) |

## TESTS (TDD — write first)

### New test class: `TestStartJobHttpErrorMessages`

```python
class TestStartJobHttpErrorMessages:
    """Tests for clean HTTP error messages in start_job."""

    @pytest.mark.parametrize("status_code,reason,expected_hint", [
        (409, "Conflict", " (job may be disabled, already queued, or running)"),
        (500, "Internal Server Error", ""),
    ])
    def test_start_job_http_error_clean_message(self, status_code, reason, expected_hint):
        """HTTP errors produce clean message with appropriate hint, no URL."""

    def test_start_job_http_error_no_response(self):
        """HTTPError without response falls back to str(e)."""

```

Each test mocks `build_job` to raise a `requests.exceptions.HTTPError` with a mock `response` object containing `status_code` and `reason`, then asserts the `JenkinsError` message matches the expected clean format and does NOT contain `buildWithParameters` or URL fragments.

## LLM PROMPT

```
Implement step 1 of issue #626. Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

TDD approach:
1. First, add the test class `TestStartJobHttpErrorMessages` to tests/utils/jenkins_operations/test_client.py
2. Then, implement `_http_error_hint()` and update the `start_job()` except block in src/mcp_coder/utils/jenkins_operations/client.py
3. Run all three code quality checks (pylint, pytest, mypy) and fix any issues

Key details:
- Import HTTPError from requests.exceptions
- In the except block, check isinstance(e, HTTPError) and e.response is not None
- Extract status_code and reason from e.response
- Use _http_error_hint() for known status code hints
- Keep non-HTTP error handling unchanged
- Tests should verify the URL is NOT in the error message
```

## COMMIT

```
fix(jenkins): clean error messages for HTTP failures in start_job

Strip URL-encoded parameters from Jenkins HTTP error messages and add
human-readable hints for known status codes (e.g., 409 Conflict).

Closes #626
```
