# Implementation Summary: LangChain Provider Support (#507)

## Overview

Adds LangChain as an **optional** second LLM provider, allowing users to use
OpenAI GPT, Google Gemini, and other models via a new `[llm]` config section.
The existing Claude provider and all existing behaviour are **untouched**.

---

## Architectural / Design Changes

### 1. New provider package

`src/mcp_coder/llm/providers/langchain/` mirrors the existing
`src/mcp_coder/llm/providers/claude/` pattern:

| File | Responsibility |
|---|---|
| `__init__.py` | Single entry point `ask_langchain()`, config loading, backend dispatch |
| `openai.py` | `ChatOpenAI` backend |
| `gemini.py` | `ChatGoogleGenerativeAI` backend |

Adding a new backend in future = add one file + one import-linter `ignore_imports` line.

### 2. Session history persisted to disk

Claude stores conversation history **server-side**; LangChain does not.
mcp-coder must persist the message list between process runs.

Two functions are added to the **existing** `session_storage.py`
(no new module, no new config file):

```
store_langchain_history(session_id, messages) → path
load_langchain_history(session_id)            → messages ([] on first call)
```

Storage location: `~/.mcp_coder/sessions/langchain/{session_id}.json`

The message list is plain `list[dict[str, str]]` (role/content pairs) so that
`session_storage.py` has zero dependency on LangChain types — import isolation
is preserved.

### 3. Provider routing (minimal change to interface.py)

One `if` block added to `prompt_llm()`, placed **before** the
`try/except TimeoutExpired` that wraps Claude's subprocess calls.
Import is **lazy** so LangChain is never imported at module load time.
`MCP_CODER_LLM_PROVIDER` env var overrides the `provider` parameter —
useful for switching providers in CI without changing config.

- `timeout` is **forwarded** to the LangChain client constructor (e.g. `ChatOpenAI(timeout=timeout)`).
- `env_vars` are **applied** via `os.environ.update(env_vars)` before the backend call.
  Priority: `env_vars` param > system env var > config file `api_key`.
- `method` parameter is **silently ignored** (LangChain always uses direct API).
- `execution_dir`, `mcp_config`, `branch_name` are also silently ignored
  (Claude-specific parameters).

### 4. Config loading (no new config module)

Config is read inline in `langchain/__init__.py` via the existing
`get_config_values()`. No new dataclass, no new loader file.

```toml
[llm]
provider = "langchain"

[llm.langchain]
backend     = "openai"
model       = "gpt-4o"
api_key     = "sk-..."       # optional — env var takes priority
endpoint    = "..."          # optional; base_url for OpenAI, azure_endpoint for Azure
api_version = "2024-02-01"   # optional — presence triggers AzureChatOpenAI
```

Env var priority (checked before config file):
- `OPENAI_API_KEY` overrides `[llm.langchain] api_key` for the openai backend
- `GEMINI_API_KEY` overrides `[llm.langchain] api_key` for the gemini backend

This is handled inside each backend module with a simple `os.getenv()` check.

### 5. Library isolation (one new import-linter contract)

A **single** contract in `.importlinter` forbids `langchain_core`,
`langchain_openai`, and `langchain_google_genai` everywhere except
`mcp_coder.llm.providers.langchain.**` — identical pattern to
`claude_sdk_isolation`.

### 6. LLMResponseDict compatibility

LangChain provider returns the **standard** `LLMResponseDict`. No changes to
the type. `raw_response` holds a serialisable dict built from LangChain's
`AIMessage` (content, response_metadata, usage_metadata, id).
`MLflowLogger` works as-is because it only consumes `LLMResponseDict`.

---

## Files to Create

| File | Purpose |
|---|---|
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Entry point, config loading, dispatch |
| `src/mcp_coder/llm/providers/langchain/openai.py` | OpenAI backend |
| `src/mcp_coder/llm/providers/langchain/gemini.py` | Gemini backend |
| `src/mcp_coder/llm/providers/langchain/_utils.py` | Shared message conversion helpers |
| `tests/llm/providers/langchain/__init__.py` | Test package marker |
| `tests/llm/providers/langchain/test_langchain_provider.py` | Tests for `__init__.py` |
| `tests/llm/providers/langchain/test_langchain_openai.py` | Tests for `openai.py` |
| `tests/llm/providers/langchain/test_langchain_gemini.py` | Tests for `gemini.py` |
| `tests/llm/providers/langchain/conftest.py` | `sys.modules` mocks for unit tests |
| `tests/llm/providers/langchain/test_langchain_integration.py` | LangChain integration tests (Step 3b) |

---

## Files to Modify

| File | Change |
|---|---|
| `pyproject.toml` | Add `langchain` optional extra; add mypy overrides; add `langchain_integration` pytest marker |
| `.importlinter` | Add single LangChain isolation contract |
| `src/mcp_coder/llm/storage/session_storage.py` | Add `store_langchain_history()`, `load_langchain_history()`, `_langchain_session_path()` |
| `src/mcp_coder/llm/interface.py` | Add `elif provider == "langchain":` branch; update unsupported-provider error message |
| `tests/llm/storage/test_session_storage.py` | Add tests for the two new history functions |
| `tests/llm/providers/test_provider_structure.py` | Assert langchain package is present |
| `docs/configuration/config.md` | Document `[llm]` and `[llm.langchain]` sections |
| `docs/architecture/architecture.md` | Update LLM provider section; add session storage subsection |

---

## Step Overview

| Step | Title | Contains tests? |
|---|---|---|
| 1 | Project configuration (`pyproject.toml` + `.importlinter`) | No |
| 2 | Session history storage (extend `session_storage.py`) | Yes (TDD) |
| 3 | LangChain provider package | Yes (TDD) |
| 3b | LangChain integration tests | Yes (integration, skipped if unconfigured) |
| 4 | Interface routing (`interface.py`) | Yes (TDD) |
| 5 | Documentation | No |
