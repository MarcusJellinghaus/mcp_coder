# Step 5: Test cleanup + shim test

**Commit message:** `adopt mcp-coder-utils: delete migrated tests, add log suppression shim test`

> **Context:** See `pr_info/steps/summary.md` for the full plan (issue #744).
> This step deletes test files whose coverage now lives in mcp-coder-utils and adds one small test for the log suppression wrapper.

## WHERE

### Delete
- `tests/utils/test_subprocess_runner.py`
- `tests/utils/test_subprocess_runner_real.py`
- `tests/utils/test_subprocess_streaming.py`
- `tests/utils/test_log_utils.py`
- `tests/utils/test_log_utils_redaction.py`

### Create
- `tests/utils/test_log_utils_shim.py`

## WHAT

### Deletions
These 5 test files test the core implementations that now live in `mcp-coder-utils`. The shared library has its own test suite. Keeping them here would be redundant and would break (e.g., `_redact_for_logging` is no longer exported).

### New test: `test_log_utils_shim.py`
One small test verifying the app-specific log suppression in the `setup_logging()` wrapper works correctly.

## HOW

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

## ALGORITHM

```
1. Delete 5 test files
2. Create test_log_utils_shim.py with 4 simple assertions
3. Run pytest to verify new test passes and no other tests broke
```

## DATA

No data structures. Pure assertions on logger levels.

## VERIFICATION

- All 4 shim tests pass
- No test collection errors from deleted files
- Total test count decreases (deleted tests) + 4 new tests
- Run pylint, mypy, pytest

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md.

Implement step 5: Delete the 5 test files listed (test_subprocess_runner.py,
test_subprocess_runner_real.py, test_subprocess_streaming.py, test_log_utils.py,
test_log_utils_redaction.py). Create tests/utils/test_log_utils_shim.py with
tests verifying log suppression. Run all checks after.
```
