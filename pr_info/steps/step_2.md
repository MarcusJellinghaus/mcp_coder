# Step 2: log_utils shim

**Commit message:** `adopt mcp-coder-utils: log_utils shim + delete broken log tests + add shim test`

> **Context:** See `pr_info/steps/summary.md` for the full plan (issue #744).
> This step replaces `log_utils.py` with a thin re-export shim that wraps `setup_logging()` with app-specific third-party log suppression.

## WHERE

- `src/mcp_coder/utils/log_utils.py` — replace body
- `tests/utils/test_log_utils.py` — delete
- `tests/utils/test_log_utils_redaction.py` — delete
- `tests/utils/test_log_utils_shim.py` — create

## WHAT

Replace the entire file body with:
1. Re-exports from `mcp_coder_utils.log_utils` — all public symbols
2. Re-exports from `mcp_coder_utils.redaction` — `REDACTED_VALUE`, `RedactableDict` and formatter classes
3. A wrapped `setup_logging()` that calls the upstream version, then adds app-specific third-party log suppression

### Symbols to re-export from `mcp_coder_utils.log_utils`
- `OUTPUT` (custom log level = 25)
- `STANDARD_LOG_FIELDS`
- `CleanFormatter`, `ExtraFieldsFormatter`
- `log_function_call`
- `setup_logging` as `_upstream_setup_logging` (renamed, wrapped locally)

### Symbols to re-export from `mcp_coder_utils.redaction`
- `REDACTED_VALUE`, `RedactableDict`

### Local wrapper: `setup_logging()`
Calls `_upstream_setup_logging(log_level, log_file)`, then suppresses:
- `urllib3.connectionpool` → INFO
- `github.Requester` → INFO  
- `httpx` → WARNING
- `httpcore` → WARNING

### NOT re-exported
- `_redact_for_logging` — not re-exported because `log_function_call` (which uses it internally) is itself re-exported from `mcp_coder_utils`; the local helper is no longer needed

### Delete 2 log_utils test files
These test files must be deleted in this same step because they break immediately once the shim replaces the full implementation:
- `test_log_utils_redaction.py` — imports `_redact_for_logging` which the shim doesn't re-export
- `test_log_utils.py` — tests internal implementation details (structlog processors, JSON formatter config) that no longer exist in the shim

Core test coverage for these modules now lives in the `mcp-coder-utils` package.

### New test: `test_log_utils_shim.py`
One small test verifying the app-specific log suppression in the `setup_logging()` wrapper works correctly.

## HOW

```python
from mcp_coder_utils.log_utils import (
    OUTPUT, STANDARD_LOG_FIELDS, CleanFormatter, ExtraFieldsFormatter,
    log_function_call,
    setup_logging as _upstream_setup_logging,
)
from mcp_coder_utils.redaction import REDACTED_VALUE, RedactableDict
```

No imports of `structlog`, `pythonjsonlogger`, `json`, `os`, `time`, `functools`, etc.

## ALGORITHM

```python
def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """Configure logging with app-specific third-party log suppression."""
    _upstream_setup_logging(log_level, log_file)
    # App-specific: suppress noisy third-party loggers
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
    logging.getLogger("github.Requester").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
```

## ALGORITHM (test deletions + shim test creation)

```
1. Delete tests/utils/test_log_utils.py
2. Delete tests/utils/test_log_utils_redaction.py
3. Create tests/utils/test_log_utils_shim.py with the following content:
```

```python
"""Tests for log_utils shim — verifies app-specific log suppression."""

import logging

from mcp_coder.utils.log_utils import setup_logging


class TestLogSuppressionShim:
    """Verify setup_logging() suppresses noisy third-party loggers."""

    def test_urllib3_suppressed_after_setup(self) -> None:
        """urllib3.connectionpool should be at INFO after setup_logging()."""
        setup_logging("DEBUG")
        assert logging.getLogger("urllib3.connectionpool").level == logging.INFO

    def test_httpx_suppressed_after_setup(self) -> None:
        """httpx should be at WARNING after setup_logging()."""
        setup_logging("DEBUG")
        assert logging.getLogger("httpx").level == logging.WARNING

    def test_httpcore_suppressed_after_setup(self) -> None:
        """httpcore should be at WARNING after setup_logging()."""
        setup_logging("DEBUG")
        assert logging.getLogger("httpcore").level == logging.WARNING

    def test_github_suppressed_after_setup(self) -> None:
        """github.Requester should be at INFO after setup_logging()."""
        setup_logging("DEBUG")
        assert logging.getLogger("github.Requester").level == logging.INFO
```

## DATA

No new data structures. All types come from `mcp_coder_utils`.

`__all__` should list: `OUTPUT`, `STANDARD_LOG_FIELDS`, `CleanFormatter`, `ExtraFieldsFormatter`, `log_function_call`, `setup_logging`, `REDACTED_VALUE`, `RedactableDict`

## VERIFICATION

- All existing imports (`from mcp_coder.utils.log_utils import ...`) still resolve
- Remaining tests pass (deleted tests no longer cause import errors)
- All 4 shim tests pass
- The shim no longer imports `structlog` or `pythonjsonlogger` directly
- Run pylint, mypy, pytest

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement step 2: Replace log_utils.py with a thin re-export shim over
mcp_coder_utils.log_utils and mcp_coder_utils.redaction. Wrap setup_logging()
to add app-specific third-party log suppression (urllib3, github, httpx, httpcore).
Do NOT re-export _redact_for_logging. Also delete tests/utils/test_log_utils.py
and tests/utils/test_log_utils_redaction.py (they test internals no longer in the
shim). Create tests/utils/test_log_utils_shim.py with 4 log suppression assertions.
Do NOT modify any other files. Run all checks after.
```
