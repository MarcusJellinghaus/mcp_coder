# Step 3 — Part B: shared prompt-path 404 hint helper

See `pr_info/steps/summary.md` for context. This step de-duplicates the 404
handling copy-pasted in `_ask_text` and `_ask_text_stream`, and — when a custom
`endpoint` is configured — replaces the misleading "model not found" message
with a base-URL hint, while skipping the wasted `list_openai_models` round-trip.

## WHERE

- `src/mcp_coder/llm/providers/langchain/__init__.py` — new helper + both call
  sites.
- `tests/llm/providers/langchain/test_langchain_provider.py` — `_ask_text` tests.
- `tests/llm/providers/langchain/test_langchain_streaming.py` — `_ask_text_stream`
  tests.

## WHAT

New helper in `__init__.py` (place near `_get_model_suggestions`):

```python
def _format_404_hint(config: dict[str, str | None]) -> str:
    """Build the user-facing hint for a 404 / model-not-found response.

    For a custom OpenAI-compatible endpoint the likely cause is a wrong base
    URL, so return a base-URL hint and skip the model-listing round-trip.
    Otherwise fall back to 'model not found' plus best-effort suggestions.
    """
```

## HOW (integration)

Replace the duplicated 404 blocks.

`_ask_text` — inside `except Exception as exc:`, after `_handle_provider_error`:

```python
exc_lower = str(exc).lower()
if "404" in exc_lower or "not_found" in exc_lower or "not found" in exc_lower:
    raise ValueError(_format_404_hint(config)) from exc
raise
```

`_ask_text_stream` — inside its `except Exception as exc:` (after the
`TimeoutError` re-raise and `_handle_provider_error`):

```python
exc_lower = str(exc).lower()
if "404" in exc_lower or "not_found" in exc_lower or "not found" in exc_lower:
    hint = _format_404_hint(config)
    yield {"type": "error", "message": hint}
    raise ValueError(hint) from exc
yield {"type": "error", "message": str(exc)}
raise
```

## ALGORITHM (core logic of `_format_404_hint`)

```
model = config.get("model", "")
if config.get("endpoint") and not config.get("api_version"):   # custom relay
    return (f"Model {model!r} not found. If using a custom server, check your "
            "base URL (e.g. …/v1); mcp-coder appends /chat/completions.")
hint = f"Model {model!r} not found."                           # default / Azure
try:
    hint += _get_model_suggestions(config)
except Exception:      # pylint: disable=broad-except
    pass
return hint
```

The custom-endpoint branch never calls `_get_model_suggestions`, so the wasted
`list_openai_models` round-trip is skipped. Azure (api_version set) falls through
to the default branch.

## DATA

`_format_404_hint` returns a `str`. `_ask_text` raises `ValueError(hint)`;
`_ask_text_stream` yields `{"type": "error", "message": hint}` then raises
`ValueError(hint)`. No change to `LLMResponseDict` or `StreamEvent` shapes.

## TESTS (write first)

In `test_langchain_provider.py` (mirror the existing `_ask_text` error tests —
mock `_load_langchain_config`, `_create_chat_model`, history load/store):

- 404 from `invoke()` with `endpoint="https://h/v1"` set →
  `ValueError` message contains "base URL" and "/chat/completions"; assert
  `list_openai_models` (patched) is **not** called.
- 404 with `endpoint=None` → message contains "not found"; suggestions path is
  taken (`_get_model_suggestions` / `list_openai_models` invoked).

In `test_langchain_streaming.py` (mirror existing `_ask_text_stream` tests):

- 404 during `stream()` with a custom `endpoint` → an `{"type": "error"}` event
  is yielded whose message contains "base URL", then `ValueError` is raised;
  `list_openai_models` is **not** called.
- 404 with `endpoint=None` → error event + `ValueError` with "not found".

Both files should confirm the two paths share `_format_404_hint` (identical
wording), guarding against future drift.

## LLM PROMPT

> Implement Step 3 from `pr_info/steps/step_3.md` (context in
> `pr_info/steps/summary.md`). Work test-first.
>
> 1. Add tests: in
>    `tests/llm/providers/langchain/test_langchain_provider.py` for `_ask_text`
>    and in `tests/llm/providers/langchain/test_langchain_streaming.py` for
>    `_ask_text_stream`, covering the custom-endpoint 404 (base-URL hint, no
>    `list_openai_models` call) and the no-endpoint 404 (model-not-found +
>    suggestions), per step_3.md.
> 2. Add `_format_404_hint(config)` to
>    `src/mcp_coder/llm/providers/langchain/__init__.py` per the ALGORITHM.
> 3. Replace the duplicated 404 blocks in `_ask_text` and `_ask_text_stream`
>    with calls to `_format_404_hint`, preserving the stream path's
>    `yield {"type": "error", ...}` then `raise ValueError(...)` shape.
>
> Use MCP file tools only. After editing, run `run_pylint_check`,
> `run_pytest_check` (fast `-n auto` + `not …integration` exclusions), and
> `run_mypy_check`; fix any issues. This is one commit.
