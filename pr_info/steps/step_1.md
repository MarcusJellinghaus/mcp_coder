# Step 1 — `_exceptions.py`: narrow tuple, add LLMMCPLaunchError, gate SSL hint, un-quote install hint

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement
> Step 1 only: update
> `src/mcp_coder/llm/providers/langchain/_exceptions.py` and its tests
> (`tests/llm/providers/langchain/test_langchain_exceptions.py`,
> `tests/llm/providers/langchain/test_langchain_diagnostics.py`) to narrow
> `CONNECTION_ERRORS`, add `LLMMCPLaunchError`, gate the SSL hint on
> classification, remove the duplicate truststore hint from
> `format_diagnostics`, and un-quote the `pip install` hint at both call
> sites. Run the mandatory MCP tool quality checks (pylint, pytest, mypy).
> Do not touch `agent.py` or `verification.py`.

## WHERE

- `src/mcp_coder/llm/providers/langchain/_exceptions.py` — modify.
- `tests/llm/providers/langchain/test_langchain_exceptions.py` — modify.
- `tests/llm/providers/langchain/test_langchain_diagnostics.py` — modify.

## WHAT

### New exception

```python
class LLMMCPLaunchError(Exception):
    """Local MCP subprocess launch failed (binary missing / permission)."""
```

### Narrow `CONNECTION_ERRORS`

```python
try:
    import httpx
    CONNECTION_ERRORS: tuple[type[Exception], ...] = (
        httpx.ConnectError,
        httpx.ConnectTimeout,
        ConnectionError,
    )
except ImportError:
    CONNECTION_ERRORS = (ConnectionError,)
```

`OSError` is **removed**. `LLMMCPLaunchError` is **not** added.

### Un-quote `_SSL_HINT`

`pip install 'mcp-coder[truststore]'` → `pip install mcp-coder[truststore]`.

> **Out-of-scope note (Boy Scout):**
> `src/mcp_coder/llm/providers/langchain/_models.py` contains 3
> single-quoted `pip install 'mcp-coder[langchain]'` ImportError hints
> (lines ~45, ~81, ~119). These are pre-existing and **out of scope** for
> issue #830; flagged for a future Boy Scout fix so future reviewers
> don't re-flag.

### Gate SSL hint in `raise_connection_error`

Before `lines.append(_SSL_HINT)`, check classification:

```python
if classify_connection_error(original).startswith("ssl-error"):
    lines.append(_SSL_HINT)
```

(Move `_SSL_HINT` append under this guard; delete the unconditional
append.)

### Strip truststore hint from `format_diagnostics`

Delete the `if not truststore_active:` block that adds
`"Hint: Install truststore ... pip install 'mcp-coder[truststore]' ..."`.
Keep the `Truststore active: <bool>` line and the `HTTPS_PROXY` hint for
missing proxy.

## HOW — integration points

- `_SSL_HINT` already imported implicitly within the module; no external
  imports change.
- `classify_connection_error` is defined lower in the same file. Since
  Python defers name resolution to call time, calling it from
  `raise_connection_error` works without reordering.
- Public export surface gains `LLMMCPLaunchError`. It is imported in
  Step 2 (`agent.py`) — no re-export needed elsewhere this step.

## ALGORITHM — SSL-gating

```
build lines = ["Connection to <P> API failed: ...", "Check:", ...]
append env-var / endpoint / network lines
if classify_connection_error(original).startswith("ssl-error"):
    append _SSL_HINT
raise LLMConnectionError("\n".join(lines)) from original
```

## DATA

- `CONNECTION_ERRORS`: `tuple[type[Exception], ...]` of length 3 (httpx
  available) or 1 (fallback).
- `LLMMCPLaunchError`: subclass of `Exception` only.
- `raise_connection_error`: still `NoReturn`; message omits SSL block for
  non-SSL errors.
- `format_diagnostics`: returns multi-line string with `Error category`,
  `Proxy configured`, `Truststore active`, and optional `HTTPS_PROXY`
  hint — **no** truststore hint line.

## TDD — tests to add / change

In `test_langchain_exceptions.py`:

1. **Change `test_connection_errors_contains_oserror`** → assert
   `OSError not in CONNECTION_ERRORS` and
   `ConnectionError in CONNECTION_ERRORS`. Optionally also assert
   `httpx.ConnectError in CONNECTION_ERRORS` (guard the assertion with a
   `try: import httpx` skip).
2. **Change `test_message_contains_ssl_hint`** → pass
   `ssl.SSLError("certificate verify failed")` as `original`. Assert
   `"truststore"` in the message and assert the hint uses **unquoted**
   form `pip install mcp-coder[truststore]` (no single quotes around
   `mcp-coder[truststore]`).
3. **New `test_no_ssl_hint_for_non_ssl_error`** → pass
   `ConnectionRefusedError("refused")`; assert `"truststore"` **not in**
   the message.
4. **New `test_llm_mcp_launch_error_hierarchy`** → assert
   `issubclass(LLMMCPLaunchError, Exception)`,
   `not issubclass(LLMMCPLaunchError, ConnectionError)`,
   `LLMMCPLaunchError not in CONNECTION_ERRORS`.
5. **New `test_handle_provider_error_passes_through_filenotfound`** and
   **`..._passes_through_permission_error`** — call
   `mcp_coder.llm.providers.langchain._handle_provider_error(
     FileNotFoundError("nope"), "openai")` and assert the function
   returns `None` without raising. Same for `PermissionError`.

In `test_langchain_diagnostics.py`:

6. **Change `test_truststore_not_available_shows_hint`** → assert the
   diagnostic string contains `"Truststore active: False"` and does
   **not** contain `"pip install"` or `"Install truststore"`. Rename to
   `test_truststore_not_available_omits_install_hint`.

No tests are renamed or removed beyond (6). Existing tests that pass
`OSError(...)` as `original` to `raise_connection_error` remain valid —
they don't assert against `CONNECTION_ERRORS` and the helper only
stringifies `original`.

## Done-when

- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_pytest_check` (fast-unit marker exclusions) green.
- `mcp__tools-py__run_mypy_check` clean.
- Single commit: "Step 1: narrow CONNECTION_ERRORS, add LLMMCPLaunchError,
  gate SSL hint (#830)".
