# Step 5: Catch specific exceptions in `verification.py`

> **Context**: See `pr_info/steps/summary.md` for the full issue and architecture.

## Goal

Replace the broad `except Exception` in `_list_models_for_backend()` with specific catches for `LLMConnectionError` and `LLMAuthError` for better diagnostic output in `mcp-coder verify --check-models`. Keep a fallback `except Exception` for unexpected errors.

## LLM Prompt

```
Implement Step 5 of Issue #555 (see pr_info/steps/summary.md for full context).

Update _list_models_for_backend() in verification.py to catch LLMConnectionError and LLMAuthError
specifically for better diagnostic output. Write tests first (TDD), then implementation.
Run all code quality checks after.
Follow the specifications in this step file exactly.
```

## WHERE

- **Modified**: `src/mcp_coder/llm/providers/langchain/verification.py`
- **Modified tests**: `tests/llm/providers/langchain/test_langchain_verification.py`

## WHAT

### Import added to `verification.py`

```python
from ._exceptions import LLMAuthError, LLMConnectionError
```

### Changes to `_list_models_for_backend()`

Replace the single broad `except Exception` with three ordered except clauses:

```python
def _list_models_for_backend(backend, api_key, endpoint):
    try:
        from . import _models
        # ... existing model listing logic ...
        return {"ok": True, "value": models}
    except LLMConnectionError as exc:
        return {"ok": False, "value": [], "error": str(exc), "error_type": "connection"}
    except LLMAuthError as exc:
        return {"ok": False, "value": [], "error": str(exc), "error_type": "auth"}
    except Exception as exc:
        return {"ok": False, "value": [], "error": str(exc), "error_type": "unknown"}
```

### New field: `error_type`

The result dict gains an `error_type` field (`"connection"`, `"auth"`, or `"unknown"`) so the CLI layer can format diagnostic output differently if needed. This is additive — existing callers that don't check `error_type` are unaffected.

## ALGORITHM

### `_list_models_for_backend` (updated)
```
1. Try: import _models, call appropriate list function, return ok=True with models
2. Except LLMConnectionError: return ok=False with error message and error_type="connection"
3. Except LLMAuthError: return ok=False with error message and error_type="auth"
4. Except Exception: return ok=False with error message and error_type="unknown" (fallback)
```

## DATA

### Updated return dict structure
```python
{
    "ok": bool,
    "value": list[str],       # model names (empty on error)
    "error": str,              # error message (only on error)
    "error_type": str,         # "connection" | "auth" | "unknown" (only on error)
}
```

## HOW

- `LLMConnectionError` and `LLMAuthError` are raised by `_models.py` (wrapped in Step 3)
- The `str(exc)` already contains the full multi-line hint message from `_exceptions.py`
- The pylint `broad-exception-caught` disable comment can be removed from the `LLMConnectionError`/`LLMAuthError` catches, but should remain on the fallback `except Exception`

## Tests (added to `test_langchain_verification.py`)

### New test class

**`TestListModelsForBackendErrors`**
- `test_connection_error_returns_error_type_connection` — mock `_models.list_openai_models` to raise `LLMConnectionError`, verify `error_type == "connection"`
- `test_auth_error_returns_error_type_auth` — mock to raise `LLMAuthError`, verify `error_type == "auth"`
- `test_unknown_error_returns_error_type_unknown` — mock to raise generic `RuntimeError`, verify `error_type == "unknown"`
- `test_connection_error_message_preserved` — verify the full hint message is in the `error` field
- `test_auth_error_message_preserved` — verify the full hint message is in the `error` field
- `test_success_has_no_error_type` — verify successful result has no `error_type` key (additive, not breaking)

### Existing tests unchanged
- `TestVerifyLangchain.test_check_models_flag` uses `_list_models_for_backend` mock — unaffected
- All other verification tests don't touch `_list_models_for_backend` directly
