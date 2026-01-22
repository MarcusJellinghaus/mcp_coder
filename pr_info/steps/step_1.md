# Step 1: Add urllib3.connectionpool Logger Suppression

## LLM Prompt

```
Implement Issue #315: Suppress DEBUG logs from urllib3.connectionpool.

Reference: pr_info/steps/summary.md

Add suppression for urllib3.connectionpool DEBUG logs in the setup_logging() function.
The change should include a code comment and a DEBUG log message for discoverability.
```

## WHERE

- **File**: `src/mcp_coder/utils/log_utils.py`
- **Function**: `setup_logging()`
- **Location**: After the loop that sets all logger levels (around line 145), before handler setup

## WHAT

No new functions. Add 4 lines of code inside existing `setup_logging()` function:

Suppression code (after line ~145):
```python
# Suppress verbose DEBUG logs from urllib3 connection pool
# These logs obscure meaningful debug output from project loggers
logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
```

Log message (at end of function, after handler setup):
```python
stdlogger.debug("Suppressing DEBUG logs from: urllib3.connectionpool")
```

## HOW

Insert the suppression code after line ~145 (after the loop that sets all logger levels) and before the `# Set up logging based on whether log_file is specified` comment.

Add the DEBUG log message at the end of the function, after all handler setup is complete (this ensures the message is visible regardless of logging mode).

**Integration**: Uses existing `logging` import and `stdlogger` module-level logger.

## ALGORITHM

```
1. Get logger for "urllib3.connectionpool"
2. Set its level to INFO (suppresses DEBUG, allows INFO/WARNING/ERROR)
3. Log DEBUG message indicating suppression (for discoverability)
```

## DATA

- **Input**: None (hardcoded logger name)
- **Output**: None (side effect: logger level modified)
- **Return value**: N/A (function returns None)

## VERIFICATION

Run existing tests to confirm no regressions:
```bash
pytest tests/utils/test_log_utils.py -v
```

The existing tests already verify that:
- Console logging works correctly
- File logging works correctly
- Log levels are set properly
- The setup_logging function doesn't raise errors

No new tests are required because:
1. The behavior is a simple configuration change (4 lines)
2. Existing tests cover the setup_logging function
3. The acceptance criteria says "Tests pass" not "Add new tests"
