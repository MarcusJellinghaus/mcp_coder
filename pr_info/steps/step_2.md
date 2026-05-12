# Step 2 — Model listing + NOT_FOUND substring extension

This step adds Ollama model listing via the `ollama` Python client and
wires it into both NOT_FOUND error hints (in `_ask_text` /
`_ask_text_stream`) and the verify `--check-models` path (in
`_list_models_for_backend`). The substring match that triggers the
hint is extended to catch Ollama's "model 'X' not found" wording.

## WHERE

**Modify:**
- `src/mcp_coder/llm/providers/langchain/_models.py` — add
  `list_ollama_models()`.
- `src/mcp_coder/llm/providers/langchain/__init__.py` — extend
  `_get_model_suggestions()` with an `"ollama"` branch; extend the
  NOT_FOUND substring match in `_ask_text()` and `_ask_text_stream()`.
- `src/mcp_coder/llm/providers/langchain/verification.py` — extend
  `_list_models_for_backend()` with an `"ollama"` branch.
- `tests/llm/providers/langchain/test_langchain_models.py` — add
  `TestListOllamaModels` class.
- `tests/llm/providers/langchain/test_langchain_provider.py` — add the
  new `"model 'foo' not found"` wording as an additional parametrize
  case on the existing NOT_FOUND test (at `test_langchain_provider.py:262`,
  `test_404_error_raises_value_error_with_model_hint`), rather than
  adding a separate standalone test.

## WHAT

```python
# _models.py
def list_ollama_models(
    api_key: str | None,
    endpoint: str | None = None,
) -> list[str]:
    """Return sorted model names from the Ollama daemon's /api/tags."""
```

## HOW

- `list_ollama_models()` mirrors `list_anthropic_models()` exactly:
  deferred SDK import (`ollama`), instantiate client, list models,
  wrap network/auth failures in `LLMConnectionError` via the existing
  `raise_connection_error` helper.
- `endpoint` is passed through `_resolve_ollama_host()` (added in
  Step 1) before being handed to `ollama.Client(host=...)`.
- `_get_model_suggestions()` adds:
  ```python
  elif backend == "ollama":
      models = list_ollama_models(
          os.getenv("OLLAMA_API_KEY") or api_key, endpoint
      )
  ```
- The NOT_FOUND substring set is updated in two places (both
  `_ask_text()` and `_ask_text_stream()`):
  ```python
  exc_lower = exc_str.lower()
  if ("404" in exc_lower
      or "not_found" in exc_lower
      or "not found" in exc_lower):  # NEW — catches Ollama wording
      ...
  ```
  Drop the redundant `"NOT_FOUND" in exc_str` clause (already covered
  by the `.lower()` check).
- `_list_models_for_backend()` in `verification.py` adds:
  ```python
  elif backend == "ollama":
      models = _models.list_ollama_models(api_key, endpoint)
  ```

## ALGORITHM

```
def list_ollama_models(api_key, endpoint=None):
    import ollama  # raises ImportError if not installed
    host = _resolve_ollama_host(endpoint)
    try:
        client = ollama.Client(host=host) if host else ollama.Client()
        data = client.list()
        # ollama-python returns {"models": [{"name": "...", ...}, ...]}
        return sorted(m["name"] for m in data.get("models", []))
    except CONNECTION_ERRORS as exc:
        raise_connection_error("Ollama", "OLLAMA_API_KEY", exc,
            endpoint_hint="endpoint/OLLAMA_HOST if not localhost")
```

**Note on `ollama.Client.list()` return shape:** verify the actual
attribute access (`m["name"]` vs `m.name`) against the installed
`ollama` package version — newer versions may return Pydantic models
rather than plain dicts. Adjust accessor accordingly; the rest of the
flow is unchanged.

## DATA

**`list_ollama_models` returns:** sorted `list[str]` of model names
(e.g. `["llama3:latest", "mistral:7b"]`). Empty list when the daemon
returns no models.

**`_get_model_suggestions` returns:** unchanged contract — formatted
multi-line string or empty string.

## Tests (write FIRST, TDD)

`tests/llm/providers/langchain/test_langchain_models.py` — new class
`TestListOllamaModels`, mirroring `TestListAnthropicModels`:

- `test_returns_sorted_model_names` — mock `ollama.Client().list()`
  returns two models, asserts sorted output.
- `test_passes_normalized_host_to_client` — `endpoint="127.0.0.1:11434"`
  → `ollama.Client(host="http://127.0.0.1:11434")`.
- `test_uses_default_client_when_no_endpoint` — no env, no
  `endpoint` → `ollama.Client()` called without `host`.
- `test_ollama_host_env_overrides_endpoint` — env wins over `endpoint`.
- `test_returns_empty_list_when_no_models` — empty `{"models": []}`.
- `test_connection_error_raises_llm_connection_error` — `ConnectionError`
  from `client.list()` → `LLMConnectionError`.
- `test_connection_error_message_contains_hints` — error message
  includes `"OLLAMA_API_KEY"` and `"OLLAMA_HOST"` (or `"endpoint"`).
- `test_import_error_when_sdk_not_installed` — `sys.modules["ollama"]
  = None` → `ImportError`.

Add NOT_FOUND-hint tests:
- Extend the existing test in `test_langchain_provider.py:262`
  (`test_404_error_raises_value_error_with_model_hint`) by adding a
  new parametrize case for the Ollama wording `"model 'foo' not found"`
  (regardless of case). Do NOT add a separate standalone test — the
  existing test already covers the "NOT_FOUND substring triggers
  `_get_model_suggestions`" path; the new case just exercises the
  extra substring. Mock `_get_model_suggestions` to return a sentinel
  string and assert it appears in the raised `ValueError`.

## Definition of done

- All new `TestListOllamaModels` tests pass.
- NOT_FOUND hint test passes for the new `"not found"` wording.
- Existing NOT_FOUND tests still pass (regression check).
- All three MCP code-quality checks pass.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement Step 2 only. Follow TDD: extend
tests/llm/providers/langchain/test_langchain_models.py with the new
TestListOllamaModels class FIRST, then add list_ollama_models() to
src/mcp_coder/llm/providers/langchain/_models.py.

Then add the NOT_FOUND-hint test, then update _ask_text() and
_ask_text_stream() in __init__.py to include "not found" (lowercase,
with space) in the substring set, and wire the ollama branch into
_get_model_suggestions().

Finally extend _list_models_for_backend() in verification.py with the
"ollama" branch.

Mirror the existing list_anthropic_models() shape exactly. Use
_resolve_ollama_host (from Step 1) to normalize the endpoint before
passing it to ollama.Client.

Verify the actual ollama.Client.list() return shape against the
installed library (dict-of-models vs Pydantic objects) and adjust
attribute access accordingly.

Do not modify daemon probe, capability check, agent wiring, or docs
— those land in later steps.

After the edits, run all three MCP code-quality checks and confirm
zero issues before reporting the step complete.
```
