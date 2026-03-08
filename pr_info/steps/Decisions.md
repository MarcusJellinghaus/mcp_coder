# Decisions — Issue #507 LangChain Provider Support

Decisions made during plan review discussion.

---

## D1 — `timeout` forwarded to LangChain client

**Decision:** Forward `timeout` from `interface.py` to the LangChain client constructors.

Both `ChatOpenAI` and `AzureChatOpenAI` accept a `timeout` kwarg.
`ChatGoogleGenerativeAI` also accepts `timeout`.
This keeps behaviour consistent with the Claude provider.

**Impact:** `ask_openai()` and `ask_gemini()` gain a `timeout: int = 30` parameter.
The `ask_langchain()` dispatch call passes `timeout=timeout`.

---

## D2 — Azure OpenAI support via `api_version` field

**Decision:** Extend `openai.py` with an optional `api_version` config field.
When `api_version` is set, use `AzureChatOpenAI` instead of `ChatOpenAI`.
No separate backend file or backend name needed.

**Config:**
```toml
[llm.langchain]
backend     = "openai"
model       = "gpt-4o"            # doubles as azure_deployment for Azure
endpoint    = "https://my-resource.openai.azure.com/"
api_version = "2024-02-01"        # presence triggers AzureChatOpenAI
api_key     = "..."
```

**Impact:**
- `ask_openai()` gains `api_version: str | None` parameter.
- `AzureChatOpenAI` imported alongside `ChatOpenAI` in `openai.py`.
- `_load_langchain_config()` reads `("llm.langchain", "api_version", None)`.
- Config doc table gains an `api_version` row.

---

## D3 — `env_vars` applied to `os.environ` before LangChain call

**Decision:** When `env_vars` is non-empty, apply it via `os.environ.update(env_vars)`
at the start of `ask_langchain()`, before any backend call.

Priority order for API keys:
1. `env_vars` parameter (highest — programmatic override)
2. System environment variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.)
3. Config file `api_key` value

**Impact:** `ask_langchain()` gains `if env_vars: os.environ.update(env_vars)` before history load.
`os` must be imported in `langchain/__init__.py`.

---

## D4 — Remove dead placeholder code from Step 4 test

**Decision:** Remove the no-op `with patch("mcp_coder.llm.interface.prompt_llm.__code__", ...): pass`
block from `test_routes_to_langchain_provider`. It was a leftover placeholder with no effect.
Only the working `patch("mcp_coder.llm.providers.langchain.ask_langchain", ...)` block is kept.

---

## D5 — Drop incomplete import error tests

**Decision:** Drop `test_import_error_has_install_instructions` from both
`test_langchain_openai.py` and `test_langchain_gemini.py`.

Testing `ImportError` from top-level module imports via `importlib.reload` is fragile
and produces unreliable results in parallel test runs (`-n auto`). The install hint
is a hardcoded string verified by code review.
