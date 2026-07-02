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

Two new helpers in `__init__.py` (place near `_get_model_suggestions`). Both the
404 **detection predicate** and the hint **message** must live in one place each,
so the two call sites cannot drift.

```python
def _is_404_error(exc: Exception) -> bool:
    """Return True when an exception looks like a 404 / model-not-found.

    Single source of truth for the detection predicate, shared by _ask_text
    and _ask_text_stream (previously copy-pasted inline in both).
    """


def _format_404_hint(config: dict[str, str | None]) -> str:
    """Build the user-facing hint for a 404 / model-not-found response.

    For a custom OpenAI-compatible endpoint the likely cause is a wrong base
    URL, so return a base-URL hint and skip the model-listing round-trip.
    Otherwise fall back to 'model not found' plus best-effort suggestions.
    """
```

## HOW (integration)

Replace the duplicated 404 blocks. The inline
`"404" in exc_lower or "not_found" in exc_lower or "not found" in exc_lower`
predicate is removed from both call sites and replaced by a single
`_is_404_error(exc)` call, so the detection lives in one place alongside the
message.

`_ask_text` — inside `except Exception as exc:`, after `_handle_provider_error`:

```python
if _is_404_error(exc):
    raise ValueError(_format_404_hint(config)) from exc
raise
```

`_ask_text_stream` — inside its `except Exception as exc:` (after the
`TimeoutError` re-raise and `_handle_provider_error`):

```python
if _is_404_error(exc):
    hint = _format_404_hint(config)
    yield {"type": "error", "message": hint}
    raise ValueError(hint) from exc
yield {"type": "error", "message": str(exc)}
raise
```

## ALGORITHM (core logic)

`_is_404_error` (the shared detection predicate):

```
low = str(exc).lower()
return "404" in low or "not_found" in low or "not found" in low
```

`_format_404_hint`:

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

Add a small direct unit test for `_is_404_error` (in either provider test file):
`Exception("Error code: 404 ...")`, `Exception("model NOT_FOUND")`, and
`Exception("not found")` → `True`; a non-404 `Exception("boom")` → `False`.

Both files should confirm the two paths share `_is_404_error` (detection) **and**
`_format_404_hint` (identical wording) — both the predicate and the message now
live in one place each, guarding against future drift.

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
> 2. Add `_is_404_error(exc)` and `_format_404_hint(config)` to
>    `src/mcp_coder/llm/providers/langchain/__init__.py` per the ALGORITHM.
> 3. Replace the duplicated 404 blocks in `_ask_text` and `_ask_text_stream`
>    with calls to `_is_404_error` (detection) and `_format_404_hint` (message),
>    removing the inline predicate from both sites and preserving the stream
>    path's `yield {"type": "error", ...}` then `raise ValueError(...)` shape.
>
> Use MCP file tools only. After editing, run `run_pylint_check`,
> `run_pytest_check` (fast `-n auto` + `not …integration` exclusions), and
> `run_mypy_check`; fix any issues. This is one commit.
