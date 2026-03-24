# Step 5: Improve Verify Output + Add httpx Dependency

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #562).

## Goal

1. Improve the test prompt failure message in `verify.py` to show a short summary + `--debug` hint instead of raw exception text
2. Guard `classify_connection_error` — only call it for connection-related exceptions
3. Add `httpx>=0.27.0` as an explicit dependency in the langchain extras
4. Add mypy override for httpx

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/verify.py` | **Modify** — improve test prompt failure output |
| `pyproject.toml` | **Modify** — add httpx dep + mypy override |
| `tests/cli/commands/test_verify_orchestration.py` | **Modify** — add test for improved failure message |

## WHAT — Changes

### `verify.py` — Test Prompt Failure

Current code:
```python
except Exception as exc:
    test_prompt_ok = False
    print(f"  {'Test prompt':<20s} {symbols['failure']} FAILED ({exc})")
```

New code:
```python
except Exception as exc:
    test_prompt_ok = False
    # Only classify connection-related exceptions
    if isinstance(exc, (OSError, ConnectionError)):
        try:
            from ...llm.providers.langchain._exceptions import classify_connection_error
            category = classify_connection_error(exc)
        except ImportError:
            category = "Connection error"
    else:
        category = f"{type(exc).__name__}: {exc}"
    print(f"  {'Test prompt':<20s} {symbols['failure']} FAILED ({category})")
    logger.debug("Test prompt failure details: %s", exc, exc_info=True)
    print("  Run with --debug for detailed diagnostics.")
```

### `pyproject.toml` — Dependency

Add to `[project.optional-dependencies] langchain`:
```toml
"httpx>=0.27.0",
```

Add mypy override:
```toml
[[tool.mypy.overrides]]
module = ["httpx", "httpx.*"]
ignore_missing_imports = true
```

## HOW — Integration Points

- `verify.py` checks `isinstance(exc, (OSError, ConnectionError))` before importing `classify_connection_error`
- For non-connection exceptions (e.g., `ValueError`, `RuntimeError`), it shows `type(exc).__name__: str(exc)` directly
- The `--debug` hint tells users to set logging to DEBUG for full diagnostics
- The `logger.debug(...)` with `exc_info=True` ensures the full traceback is available at DEBUG level

## ALGORITHM — Updated except block

```python
except Exception as exc:
    test_prompt_ok = False
    if isinstance(exc, (OSError, ConnectionError)):
        try:
            from ...llm.providers.langchain._exceptions import classify_connection_error
            category = classify_connection_error(exc)
        except ImportError:
            category = "Connection error"
    else:
        category = f"{type(exc).__name__}: {exc}"
    print(f"  {'Test prompt':<20s} {symbols['failure']} FAILED ({category})")
    logger.debug("Test prompt failure details: %s", exc, exc_info=True)
    print("  Run with --debug for detailed diagnostics.")
```

The `try/except ImportError` guard handles the case where langchain extras aren't installed (classify falls back to generic label).

## DATA — No new return types

`execute_verify` still returns `int`.

## TESTS — Modified in `test_verify_orchestration.py`

Write tests **first** (TDD), then implement.

### New / Modified Tests

**`TestVerifyTestPromptFailure`** (new class):
- `test_connection_error_shows_category` — mock `prompt_llm` to raise `ConnectionResetError`, verify output contains "Connection reset" not the raw traceback
- `test_non_connection_error_shows_type_and_message` — mock `prompt_llm` to raise `RuntimeError("oops")`, verify output contains "RuntimeError: oops"
- `test_failure_shows_debug_hint` — verify output contains "Run with --debug"
- `test_oserror_shows_category` — mock `prompt_llm` to raise `OSError(10054, "...")`, verify classification is used

**Existing test modification**:
- `test_test_prompt_failure_does_not_raise` — verify it still passes (no regression)

## LLM Prompt

```
Implement Step 5 of Issue #562 (see pr_info/steps/summary.md for context).

Three changes:

1. Modify `src/mcp_coder/cli/commands/verify.py`:
   - In the test prompt except block, guard classification:
     - If isinstance(exc, (OSError, ConnectionError)): use classify_connection_error(exc)
     - Otherwise: show type(exc).__name__: str(exc) directly
   - Add "Run with --debug for detailed diagnostics." hint
   - Log full exception details at DEBUG level with exc_info=True
   - Guard the langchain import with try/except ImportError

2. Modify `pyproject.toml`:
   - Add `"httpx>=0.27.0"` to `[project.optional-dependencies] langchain`
   - Add `[[tool.mypy.overrides]]` for `["httpx", "httpx.*"]` with `ignore_missing_imports = true`

3. Add tests to `tests/cli/commands/test_verify_orchestration.py`:
   - Test connection errors show classified category
   - Test non-connection errors show type:message directly
   - Test that failure output includes --debug hint

TDD approach: write tests first, then implement.
Run all three code quality checks after implementation.
```
