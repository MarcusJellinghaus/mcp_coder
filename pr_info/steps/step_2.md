# Step 2 — Create `mcp_coder.utils.ssl_setup` + relocate tests + import-linter contract

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement Step 2
> exactly as specified. Use TDD: move the existing test file first, edit it for
> the new module path and autouse fixture, then create the new module so tests
> pass. Update `.importlinter` in the same commit. Run pylint, pytest (fast
> unit pattern), mypy, and lint-imports. All must pass. This is one commit.

## WHERE

- New: `src/mcp_coder/utils/ssl_setup.py`
- Moved: `tests/llm/providers/langchain/test_langchain_ssl.py` →
  `tests/utils/test_ssl_setup.py`
- Modified: `.importlinter`

## WHAT

### New module: `mcp_coder/utils/ssl_setup.py`

Single public symbol `ensure_truststore() -> None`, plus module-level
`_injected: bool = False`. Behaviour and docstring identical to the existing
`mcp_coder/llm/providers/langchain/_ssl.py` (do not yet delete the old file —
that happens in Step 4).

```python
def ensure_truststore() -> None:
    """Activate truststore for OS certificate store integration if available.

    Idempotent — calls truststore.inject_into_ssl() at most once.
    No-op if truststore is not installed.
    """
```

### Relocated test file: `tests/utils/test_ssl_setup.py`

- Imports change to `from mcp_coder.utils import ssl_setup` and
  `from mcp_coder.utils.ssl_setup import ensure_truststore`.
- The existing `_reset()` helper method is replaced by an **autouse pytest
  fixture** at module level that resets `mcp_coder.utils.ssl_setup._injected =
  False` before each test. Remove `self._reset()` calls from every test method.
- The `caplog.at_level(..., logger=...)` calls update their logger name to
  `"mcp_coder.utils.ssl_setup"`.

```python
@pytest.fixture(autouse=True)
def _reset_injected() -> None:
    """Reset the global _injected flag before each test.

    The CLI entry call (Step 3) flips this flag to True for the lifetime of
    the pytest worker process; without this fixture, tests after CLI tests
    in the same xdist worker would see an already-injected state.
    """
    ssl_setup._injected = False
```

### `.importlinter` changes

1. **Remove** `truststore` from `langchain_transitive_isolation`'s
   `forbidden_modules` list and remove the line
   `mcp_coder.llm.providers.langchain.** -> truststore` from its `ignore_imports`
   block. Update the contract's docstring comment to reflect the 3 remaining
   transitive deps (`langchain_mcp_adapters`, `langgraph`, `httpx`).

2. **Add** a new contract block:

   ```ini
   # -----------------------------------------------------------------------------
   # Contract: Truststore Isolation
   # -----------------------------------------------------------------------------
   # The 'truststore' package is used in two roles:
   #   - mcp_coder.utils.ssl_setup: process-wide inject_into_ssl() at CLI entry
   #   - mcp_coder.llm.providers.langchain._http / _exceptions: explicit
   #     SSLContext() per-client and a diagnostic probe (neither is an injector)
   # Both are permitted; all other modules are forbidden.
   # -----------------------------------------------------------------------------
   [importlinter:contract:truststore_isolation]
   name = Truststore Isolation
   type = forbidden
   source_modules =
       mcp_coder
   forbidden_modules =
       truststore
   ignore_imports =
       mcp_coder.utils.ssl_setup -> truststore
       mcp_coder.llm.providers.langchain.** -> truststore
   ```

## HOW

- Use `mcp__workspace__move_file` to relocate the test file.
- Edit the moved test file in place (imports + autouse fixture + caplog logger
  names + drop `self._reset()` lines).
- Use `mcp__workspace__save_file` to write the new `ssl_setup.py`.
- Edit `.importlinter` to add the new contract and trim the old one.
- The old `_ssl.py` is left untouched in this step (still imported by langchain
  callers); it is removed in Step 4.

## ALGORITHM

Same as the existing `_ssl.ensure_truststore()`:
```
if _injected: return
try import truststore except ImportError: return
truststore.inject_into_ssl()
_injected = True
log debug "truststore activated: using OS certificate store"
```

## DATA

- Module exposes one function and one private flag. No new types, no new
  external API.
- Contract additions are pure config.

## TDD note

- The relocated test file fully covers the new module: install path, no-op when
  missing, idempotency, debug log on first call, no log on second call.
- Write/move the tests first, observe failure (module doesn't exist), then
  create `ssl_setup.py`.

## Acceptance for this step

- `mcp_coder.utils.ssl_setup.ensure_truststore` exists and behaves identically
  to the legacy `_ssl.ensure_truststore`.
- `tests/utils/test_ssl_setup.py` passes; the legacy
  `tests/llm/providers/langchain/test_langchain_ssl.py` no longer exists.
- `.importlinter` has the new `truststore_isolation` contract;
  `langchain_transitive_isolation` no longer mentions `truststore`.
- `lint-imports` is green.
- `pylint`, `pytest` (fast unit pattern), `mypy` all green.
