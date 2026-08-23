# Step 10 — Connection errors name the host actually dialed

"Connection error" today never says *where*. The host must be read from the
constructed client, not computed from config — config-derived values are wrong
whenever `OPENAI_BASE_URL` is set.

## WHERE

- `src/mcp_coder/llm/providers/langchain/__init__.py` —
  `_handle_provider_error` and its four call sites
- `src/mcp_coder/llm/providers/langchain/verification.py` —
  `_list_models_for_backend` connection branch
- `tests/llm/providers/langchain/test_langchain_provider.py`
- `tests/llm/providers/langchain/test_langchain_verification.py`

## WHAT

```python
def _handle_provider_error(
    exc: Exception, backend: str | None, dialed: str | None = None
) -> None:
    """Raise LLMAuthError / LLMConnectionError when *exc* matches, else return."""
```

## HOW

- `dialed` comes from `_config_diagnostics.dialed_url(chat_model)` (step 6) —
  the same reader, one implementation. `chat_model` is in scope at **all four**
  call sites (`_ask_text`, `_ask_agent`, `_ask_text_stream`, `_ask_agent_stream`),
  so no per-path plumbing is needed beyond passing the argument.
- The hint string handed to `raise_connection_error` becomes the dialed host when
  known, falling back to the existing static hint from `_BACKEND_ERROR_PARAMS`:
  ```python
  hint = f"tried {dialed}" if dialed else base_url_hint
  ```
  `_exceptions.raise_connection_error` already renders it as
  `  2. base_url: {hint}` (renamed in step 1) — no signature change there.
- `_list_models_for_backend` already receives `base_url`; its connection branch
  should name the URL it used the same way. Keep it simple: include the value in
  the existing `error` string.
- Default `dialed=None` keeps the four-argument call sites and every existing
  test valid.

## ALGORITHM

```
_ask_text(...):
    chat_model = _create_chat_model(config, timeout)
    try: ai_msg = chat_model.invoke(msgs)
    except Exception as exc:
        _handle_provider_error(exc, backend, dialed_url(chat_model))
        ...
```

## DATA

```
Connection to OpenAI API failed: [Errno 11001] getaddrinfo failed
Check:
  1. OPENAI_API_KEY env var or api_key in config.toml
  2. base_url: tried https://api.openai.com/v1/
  3. Network/firewall/proxy settings
```

## TDD

1. `_handle_provider_error(ConnectionError(...), "openai", "https://relay/v1")`
   → the raised `LLMConnectionError` message contains `https://relay/v1`.
2. `dialed=None` → message identical to today (regression guard).
3. Each of the four provider paths passes a non-`None` `dialed` when the chat
   model exposes a base URL — assert with a stub model per path.
4. `--check-models` connection failure names the base URL it used.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_10.md`.
> Implement step 10: add an optional `dialed: str | None = None` parameter to
> `_handle_provider_error`, use it to name the host actually dialed in the
> connection-error message, and thread it at **all four** call sites using
> `dialed_url(chat_model)` from `_config_diagnostics`. Do the same for the
> `--check-models` connection branch in `_list_models_for_backend`. The value
> must come from the constructed client, never from config. Keep the default
> `None` behaviour identical to today. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
