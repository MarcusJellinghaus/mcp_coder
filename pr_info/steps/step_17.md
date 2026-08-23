# Step 17 — TLS / proxy summary line

`_http.py` already decides the SSL context (truststore vs. certifi) and whether a
proxy is configured, but only at DEBUG level — invisible on a normal `verify`
run, which is exactly when a corporate-proxy user needs it.

## WHERE

- `src/mcp_coder/cli/commands/verify.py` — ENVIRONMENT section
- `tests/cli/commands/test_verify_sections_orchestration.py`

## WHAT

No new helper. The two predicates already exist and are pure:

```python
from ...llm.providers.langchain._exceptions import (
    _proxy_configured, _truststore_available,
)
```

## HOW

- Import **inside** `_print_environment_section` (lazy), matching how `verify.py`
  already imports from `_exceptions` in the test-prompt failure branch.
- Importing `_exceptions` is safe without the langchain extras: its `httpx` /
  `openai` / `anthropic` / `google.genai` imports are all behind
  `try/except ImportError`.
- `_truststore_available()` is exactly what `create_ssl_context` branches on, so
  the reported context source is faithful to what the client will build.
- Never print the proxy URL — it may contain credentials. Only the boolean.
- Informational: empty marker, no exit-code impact.

## ALGORITHM

```
ssl_src = "truststore (OS certificate store)" if _truststore_available() else "default (certifi/system)"
proxy   = "configured (HTTPS_PROXY/HTTP_PROXY)" if _proxy_configured() else "none"
print(_format_row("TLS / proxy", "", f"SSL context: {ssl_src}; proxy: {proxy}", indent=2))
```

## DATA

```
  TLS / proxy                   SSL context: truststore (OS certificate store); proxy: none
```

## TDD

1. `truststore` importable → the row names truststore.
2. Patch `_truststore_available` to return False → the row names the default
   context.
3. `HTTPS_PROXY` set (monkeypatch) → the row says configured and the value
   itself never appears in stdout.
4. No proxy vars → "none".
5. The row carries no status symbol and the exit code is unchanged.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_17.md`.
> Implement step 17: print a one-line TLS/proxy summary in the ENVIRONMENT
> section of `cli/commands/verify.py`, reusing the existing pure helpers
> `_truststore_available()` and `_proxy_configured()` from
> `llm/providers/langchain/_exceptions.py` (lazy import inside the function —
> no new helper module). Report only the boolean proxy state, never the URL.
> Informational only: empty marker, no exit-code impact. Write tests first (TDD),
> including an assertion that a proxy URL never leaks into the output.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
