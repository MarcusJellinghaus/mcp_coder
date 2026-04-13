# Step 2: log_utils shim

**Commit message:** `adopt mcp-coder-utils: log_utils shim with app-specific log suppression`

> **Context:** See `pr_info/steps/summary.md` for the full plan (issue #744).
> This step replaces `log_utils.py` with a thin re-export shim that wraps `setup_logging()` with app-specific third-party log suppression.

## WHERE

- `src/mcp_coder/utils/log_utils.py` — replace body

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
- `_redact_for_logging` — only consumer is `test_log_utils_redaction.py` which is deleted in step 5

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

## DATA

No new data structures. All types come from `mcp_coder_utils`.

`__all__` should list: `OUTPUT`, `STANDARD_LOG_FIELDS`, `CleanFormatter`, `ExtraFieldsFormatter`, `log_function_call`, `setup_logging`, `REDACTED_VALUE`, `RedactableDict`

## VERIFICATION

- All existing imports (`from mcp_coder.utils.log_utils import ...`) still resolve
- Existing tests pass (those importing from log_utils)
- The shim no longer imports `structlog` or `pythonjsonlogger` directly
- Run pylint, mypy, pytest

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement step 2: Replace log_utils.py with a thin re-export shim over
mcp_coder_utils.log_utils and mcp_coder_utils.redaction. Wrap setup_logging()
to add app-specific third-party log suppression (urllib3, github, httpx, httpcore).
Do NOT re-export _redact_for_logging. Do NOT modify any other files. Run all checks after.
```
