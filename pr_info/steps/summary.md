# Issue #626: fix(jenkins): improve error messages for Jenkins job failures

## Problem

When `start_job()` fails (e.g., HTTP 409 because a job is disabled), the error message includes the **entire URL-encoded Jenkins command** repeated across the traceback chain, producing a wall of unreadable text.

## Root Cause

In `client.py` `start_job()`, the except block does:
```python
raise JenkinsError(f"Failed to start job '{job_path}': {str(e)}") from e
```

For HTTP errors (like 409), `str(e)` from `requests.exceptions.HTTPError` includes the full URL with all URL-encoded parameters (repo URL, command script, credentials ID, etc.).

## Design Decision

**Single point of fix**: Only `client.py` needs production code changes. The `commands.py` error handling already does the right thing:
- `logger.error(..., exc_info=True)` → full traceback in log files (for debugging)
- `print(f"...: {e}", ...)` → just the exception message to stderr (for console)

The problem is entirely that `{e}` contains the giant URL. Fix the message at the source, and all downstream consumers automatically get clean output.

## Architecture / Design Changes

**No architectural changes.** This is a localized fix within the existing error handling pattern:

- **`client.py`**: Add HTTP-aware error message formatting in `start_job()`'s except block. Extract status code + reason from `HTTPError`, discard the URL, and add human-readable hints for known status codes.
- **Helper function**: `_http_error_hint()` — a simple dict lookup for known status code hints (409 → "job may be disabled, already queued, or running").
- **`commands.py`**: No changes needed (already correct).

## Exception Flow (python-jenkins library)

The `python-jenkins` library's `build_job()` → `jenkins_request()` raises:
- `requests.exceptions.HTTPError` directly for unhandled HTTP status codes (including **409**)
- `JenkinsException` for 401, 403, 500
- `NotFoundException` for 404
- `TimeoutException` for timeouts

For HTTP 409, we receive a raw `requests.exceptions.HTTPError` with a `.response` attribute.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/jenkins_operations/client.py` | Add `_http_error_hint()` helper; update `start_job()` except block to detect `HTTPError` and build clean messages |
| `tests/utils/jenkins_operations/test_client.py` | Add tests for HTTPError handling (409, 500, missing response) |

## Files NOT Modified

| File | Reason |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Already handles errors correctly: `logger.error` with `exc_info=True` for logs, `print` with just `{e}` for console |
| `src/mcp_coder/utils/jenkins_operations/models.py` | No changes needed |

## Steps

- **Step 1**: Tests + implementation for clean HTTP error messages in `client.py` `start_job()`
