# Step 5 — Refresh SSL-related documentation

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement Step 5
> exactly as specified. These are pure docstring/comment edits, no logic
> changes. Run pylint, pytest (fast unit pattern), mypy, and lint-imports. All
> must pass. This is one commit.

## WHERE

- `src/mcp_coder/llm/providers/langchain/_exceptions.py`
- `src/mcp_coder/llm/providers/langchain/gemini_backend.py`

## WHAT

### `_exceptions.py` — replace `_SSL_HINT`

The current `_SSL_HINT` (around line 73) recommends an extra that does not
exist (`pip install mcp-coder[truststore]`) — there is no such extra, and after
Step 1 `truststore` is in core deps anyway. Replace it with OS-trust-store
guidance:

```python
_SSL_HINT = (
    "For SSL errors behind a corporate proxy:\n"
    "  - Ensure your corporate root CA is installed in the OS trust store\n"
    "    (truststore reads it automatically).\n"
    "  - Or set SSL_CERT_FILE / REQUESTS_CA_BUNDLE to your corporate CA bundle."
)
```

### `gemini_backend.py` — refresh stale doc comment

The doc comment at lines 23-25 currently references `_ssl.ensure_truststore()`.
Update it to point at the new module:

```python
# Gemini SDK (google-genai) does not support custom httpx clients or SSL
# contexts. Proxy/SSL relies on the global truststore activation done at CLI
# entry by mcp_coder.utils.ssl_setup.ensure_truststore(). See issue #562.
```

## HOW

- Use `mcp__workspace__edit_file` with the exact existing strings as
  `old_string`.
- While editing `_exceptions.py`, confirm the `_truststore_available()` probe
  at ~line 228 matches the description (an `import truststore` inside the
  function). If it has been refactored, adapt the import-linter
  `truststore_isolation` allowlist accordingly.

## ALGORITHM

Pure text replacement — no algorithm.

## DATA

No data, no API changes. Logic and behaviour are unchanged.

## TDD note

These are documentation strings. No new tests; the existing exception/format
tests still pass because they don't assert on `_SSL_HINT`'s exact contents
(spot-check before editing — if any test does, update it in this step).

## Acceptance for this step

- `_SSL_HINT` no longer mentions `pip install mcp-coder[truststore]`.
- `_SSL_HINT` mentions `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE`.
- `gemini_backend.py:23-25` references `mcp_coder.utils.ssl_setup` (not `_ssl`).
- `pylint`, `pytest` (fast unit pattern), `mypy`, `lint-imports` all green.
