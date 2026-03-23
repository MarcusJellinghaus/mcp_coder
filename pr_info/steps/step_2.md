# Step 2: Optional truststore support (`_ssl.py`) and `pyproject.toml` dependency

> **Context**: See `pr_info/steps/summary.md` for the full issue and architecture.

## Goal

Create `_ssl.py` with `ensure_truststore()` and add the `truststore` optional dependency to `pyproject.toml`. This is a self-contained module with no dependencies on `_exceptions.py`.

## LLM Prompt

```
Implement Step 2 of Issue #555 (see pr_info/steps/summary.md for full context).

Create _ssl.py with ensure_truststore() helper and add truststore optional dependency to pyproject.toml.
Write tests first (TDD), then the implementation. Run all code quality checks after.
Follow the specifications in this step file exactly.
```

## WHERE

- **New**: `src/mcp_coder/llm/providers/langchain/_ssl.py`
- **New tests**: `tests/llm/providers/langchain/test_langchain_ssl.py`
- **Modified**: `pyproject.toml`

## WHAT

### `_ssl.py`

```python
def ensure_truststore() -> None:
    """Activate truststore for OS certificate store integration if available.

    Idempotent — calls truststore.inject_into_ssl() at most once.
    No-op if truststore is not installed.
    """
```

### `pyproject.toml` change

Add to `[project.optional-dependencies]`:
```toml
# OS certificate store integration — fixes SSL errors behind corporate proxies
truststore = [
    "truststore>=0.9.0",
]
```

## ALGORITHM

### `ensure_truststore`
```
1. If module-level _injected flag is True, return immediately
2. Try to import truststore
3. If ImportError, return (truststore not installed — this is expected)
4. Call truststore.inject_into_ssl()
5. Set _injected = True
6. Log activation via logger.debug("truststore activated: using OS certificate store")
```

## DATA

- `_injected: bool` — module-level flag, starts as `False`
- No return value (void)
- Side effect: calls `truststore.inject_into_ssl()` once if available

## HOW

- Uses standard `logging.getLogger(__name__)` for debug logging
- No imports from other project modules (fully self-contained)
- Will be called explicitly from `_models.py` and `__init__.py` in later steps

## Tests (`test_langchain_ssl.py`)

### Test classes and cases

**`TestEnsureTruststore`**
- `test_calls_inject_when_truststore_available` — mock `truststore` as importable, verify `inject_into_ssl()` called
- `test_noop_when_truststore_not_installed` — mock `ImportError` on import, verify no crash
- `test_idempotent_only_calls_once` — call twice, verify `inject_into_ssl()` called exactly once
- `test_logs_activation_on_first_call` — verify `logger.debug` called with "truststore" in message
- `test_does_not_log_on_second_call` — verify no debug log on second invocation

**Note**: Each test must reset the module-level `_injected` flag before running (via direct attribute set or module reload). Use `monkeypatch` to mock the import.
