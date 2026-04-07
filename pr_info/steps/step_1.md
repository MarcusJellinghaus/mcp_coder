# Step 1: LLMTimeoutError + implement latent bug fix

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## Goal
Introduce `LLMTimeoutError(TimeoutError)` in the LLM interface. Normalize both provider timeout types into this single exception. Fix the latent bug in implement where langchain timeouts are misclassified.

## WHERE

### Modified files
- `src/mcp_coder/llm/interface.py` — add exception class, update `prompt_llm()`
- `src/mcp_coder/workflows/implement/task_processing.py` — catch `LLMTimeoutError` instead of `TimeoutExpired`
- `tests/llm/test_interface.py` — add 2 normalization tests
- `tests/workflows/implement/test_task_processing.py` — add 1 langchain timeout test

## WHAT

### New class in `llm/interface.py`
```python
class LLMTimeoutError(TimeoutError):
    """Normalized timeout error for all LLM providers."""
```

### Changed function: `prompt_llm()` in `llm/interface.py`
- **Signature**: unchanged
- **Behavior change**: catch `TimeoutExpired` (claude) and `asyncio.TimeoutError` (langchain), re-raise as `LLMTimeoutError`
- Export `LLMTimeoutError` in `__all__`

### Changed function: `process_single_task()` in `implement/task_processing.py`
- **Signature**: unchanged
- **Behavior change**: catch `LLMTimeoutError` instead of `TimeoutExpired`
- Update import: remove `TimeoutExpired`, add `LLMTimeoutError` from `mcp_coder.llm.interface`

## HOW

### `prompt_llm()` change (both provider branches)
```
# In each provider's except block:
except TimeoutExpired:         # claude branch
    <existing logging>
    raise LLMTimeoutError(f"LLM request timed out after {timeout}s") from e
    # (capture the exception as `e` first)

except asyncio.TimeoutError:   # langchain branch  
    <existing logging>
    raise LLMTimeoutError(f"LLM request timed out after {timeout}s") from e
```

### `process_single_task()` change
```
# Replace:
except TimeoutExpired:
    logger.error(...)
    return False, "timeout"
# With:
except LLMTimeoutError:
    logger.error(...)
    return False, "timeout"
```

## ALGORITHM (prompt_llm timeout normalization)
```
1. Call provider (claude or langchain)
2. If provider raises its native timeout (TimeoutExpired or asyncio.TimeoutError):
3.   Log timeout details (existing logging stays)
4.   Raise LLMTimeoutError with descriptive message, chaining original exception
5. LLMTimeoutError subclasses TimeoutError, so existing `except TimeoutError:` still catches it
```

## DATA
- `LLMTimeoutError` — no new fields, just a typed marker exception
- `process_single_task` return value unchanged: `(False, "timeout")` on timeout

## Tests

### `tests/llm/test_interface.py` — 2 new + 2 updated tests
1. `test_prompt_llm_claude_timeout_raises_llm_timeout_error` — mock `ask_claude_code_cli` to raise `TimeoutExpired`, assert `LLMTimeoutError` is raised (and is also a `TimeoutError`)
2. `test_prompt_llm_langchain_timeout_raises_llm_timeout_error` — mock `ask_langchain` to raise `asyncio.TimeoutError`, assert `LLMTimeoutError` is raised

### `tests/workflows/implement/test_task_processing.py` — 1 new test
3. `test_process_single_task_llm_timeout_error` — mock `prompt_llm` to raise `LLMTimeoutError`, assert result is `(False, "timeout")`. Proves the latent bug fix works.

### Existing tests (2 updated)
- `test_prompt_llm_timeout_expired_reraised` — currently asserts `TimeoutExpired` is raised; update to assert `LLMTimeoutError`.
- `test_prompt_llm_asyncio_timeout_reraised_for_langchain` — currently asserts `asyncio.TimeoutError` is raised; update to assert `LLMTimeoutError`.

`LLMTimeoutError` is still a `TimeoutError`, so any `except TimeoutError` callers still work.

## Commit message
```
feat(llm): introduce LLMTimeoutError for normalized timeout handling

Add LLMTimeoutError(TimeoutError) to llm/interface.py. Both
TimeoutExpired (claude) and asyncio.TimeoutError (langchain)
are now re-raised as LLMTimeoutError in prompt_llm().

Update implement/task_processing.py to catch LLMTimeoutError
instead of TimeoutExpired — fixes langchain timeouts being
misclassified as GENERAL instead of LLM_TIMEOUT.
```

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_1.md.

Key points:
- Add LLMTimeoutError(TimeoutError) class to src/mcp_coder/llm/interface.py
- In prompt_llm(), catch TimeoutExpired and asyncio.TimeoutError, re-raise as LLMTimeoutError (chain with `from e`)
- Keep existing logging in the except blocks
- Update src/mcp_coder/workflows/implement/task_processing.py to import and catch LLMTimeoutError
- Update existing timeout tests that assert TimeoutExpired/asyncio.TimeoutError to assert LLMTimeoutError
- Add the 3 new tests described in the step
- Run all quality checks (pylint, pytest, mypy) and fix any issues
```
