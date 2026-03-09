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

---

## D6 — `conftest.py` for unit test isolation

**Decision:** Add `tests/llm/providers/langchain/conftest.py` that pre-injects
mock modules into `sys.modules` before any langchain code is imported.

```python
# conftest.py
import sys
from unittest.mock import MagicMock

for _mod in ["langchain_openai", "langchain_google_genai",
             "langchain_core", "langchain_core.messages"]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
```

Without this, the top-level `try/except ImportError` in `openai.py` and
`gemini.py` prevents those modules from importing when langchain packages
are not installed — breaking `patch("...openai.ChatOpenAI")` before it runs.

**Impact:** Add `tests/llm/providers/langchain/conftest.py` to Step 3's file list.

---

## D7 — Gemini dispatch test in `test_langchain_provider.py`

**Decision:** Add `test_routes_to_gemini_backend` to `TestAskLangchain`.
All existing tests mock `openai.ask_openai`; this test verifies that
`backend="gemini"` dispatches to `gemini.ask_gemini`.

**Impact:** One additional test in Step 3's `test_langchain_provider.py`.

---

## D8 — Integration test as a new Step 3b; single active config + env var override

**Decision:** Add a new Step 3b for LangChain integration tests.

- Test file: `tests/llm/providers/langchain/test_langchain_integration.py`
- Marker: `langchain_integration` (already planned in Step 1)
- Config source: single `[llm.langchain]` entry in `config.toml`
- Env var `MCP_CODER_LLM_PROVIDER` overrides `[llm] provider` (implemented in Step 4)
- Skip condition: skip if backend/model not configured or no API key found
- Calls `ask_langchain()` directly (Step 4 not required)

**Impact:** New file `pr_info/steps/step_3b.md`; summary and file lists updated.

---

## D9 — Shared helpers in `_utils.py`

**Decision:** Extract `_to_lc_messages()` and `_ai_message_to_dict()` to a
shared `src/mcp_coder/llm/providers/langchain/_utils.py` module.
Both `openai.py` and `gemini.py` import from it.

**Impact:** Add `_utils.py` to Step 3's "Files to create" table; update HOW
section of Step 3 to reference `_utils.py` instead of per-backend definitions.

---

## D10 — `TimeoutExpired` wraps Claude branch only

**Decision:** Restructure `prompt_llm()` in `interface.py` so the
`try/except TimeoutExpired` block wraps only the Claude-specific code.
The `if provider == "langchain":` block sits **before** the try block.

Also add `MCP_CODER_LLM_PROVIDER` env var support at the top of `prompt_llm()`,
applied after input validation:
```python
provider = os.environ.get("MCP_CODER_LLM_PROVIDER") or provider
```

**Impact:** Step 4's WHAT and ALGORITHM sections updated; new test added.
