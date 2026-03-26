# Step 1: Update `log_utils.py` and its test

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## Goal

Remove the `Logger.notice()` monkey-patch from `log_utils.py` and add a threshold-only comment to the NOTICE constant. Update the corresponding test.

## WHERE

- `src/mcp_coder/utils/log_utils.py`
- `tests/utils/test_log_utils.py`

## WHAT

No new functions. Two removals and one comment addition:

1. Remove `_notice()` function (lines ~41-43)
2. Remove `logging.Logger.notice = _notice` assignment (line ~45)
3. Add comment to `NOTICE = 25` explaining it is threshold-only

## HOW

Edit `log_utils.py`:
```python
# BEFORE:
# Custom NOTICE log level (between INFO=20 and WARNING=30)
NOTICE = 25
logging.addLevelName(NOTICE, "NOTICE")


def _notice(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
    if self.isEnabledFor(NOTICE):
        self.log(NOTICE, message, *args, **kwargs)


logging.Logger.notice = _notice  # type: ignore[attr-defined]

# AFTER:
# Custom NOTICE log level (between INFO=20 and WARNING=30)
# NOTICE is a threshold-only level for CLI output filtering — never log at this level.
# Use logger.info() for messages; they will be hidden when threshold is NOTICE.
NOTICE = 25
logging.addLevelName(NOTICE, "NOTICE")
```

Edit `tests/utils/test_log_utils.py`:
```python
# REMOVE this test method from TestNoticeLevel:
def test_logger_notice_method_exists(self) -> None:
    """Test that loggers have the notice() convenience method."""
    assert hasattr(logging.getLogger(), "notice")
```

## DATA

No data structure changes.

## Verification

After edits, run:
1. `mcp__tools-py__run_pylint_check` — no lint errors
2. `mcp__tools-py__run_mypy_check` — no type errors
3. `mcp__tools-py__run_pytest_check` with `extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration and not llm_integration"]`

All checks must pass. Then commit.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Implement Step 1: Update log_utils.py and its test.

1. Edit src/mcp_coder/utils/log_utils.py:
   - Remove the _notice() function and the logging.Logger.notice = _notice monkey-patch
   - Add a threshold-only comment above NOTICE = 25
   - Keep NOTICE = 25 and logging.addLevelName(NOTICE, "NOTICE") unchanged

2. Edit tests/utils/test_log_utils.py:
   - Remove the test_logger_notice_method_exists test method from TestNoticeLevel

3. Run all three code quality checks (pylint, mypy, pytest). Fix any issues.

4. Commit with message: "Remove NOTICE monkey-patch from log_utils, add threshold-only comment"
```
