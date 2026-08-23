# Step 1 — Rename `endpoint` → `base_url`

Mechanical, user-facing rename. `endpoint` stops being a recognised config key;
`MCP_CODER_LLM_LANGCHAIN_ENDPOINT` stops being read. No alias, no shim
(Decision 13). Largest step (~250 matches) but atomic — it cannot be split
without leaving the tree broken.

## WHERE

**Source (10 files)**

- `src/mcp_coder/utils/user_config.py` — `_CONFIG_SCHEMA["llm.langchain"]`
- `src/mcp_coder/llm/providers/langchain/__init__.py`
- `src/mcp_coder/llm/providers/langchain/openai_backend.py`
- `src/mcp_coder/llm/providers/langchain/ollama_backend.py`
- `src/mcp_coder/llm/providers/langchain/_models.py`
- `src/mcp_coder/llm/providers/langchain/_preflight.py`
- `src/mcp_coder/llm/providers/langchain/_errors_404.py`
- `src/mcp_coder/llm/providers/langchain/_exceptions.py`
- `src/mcp_coder/llm/providers/langchain/verification.py`
- `src/mcp_coder/cli/commands/verify_formatting.py`

**Tests (~22 files)** — every `_make_config()` helper and `endpoint=` kwarg under
`tests/llm/providers/langchain/`, plus `tests/utils/test_user_config_schema.py`
and `tests/cli/commands/test_verify_format_pad.py`.

## WHAT

```python
# user_config.py — replaces the "endpoint" entry outright
"llm.langchain": {
    ...
    "base_url": FieldDef(str, env_var="MCP_CODER_LLM_LANGCHAIN_BASE_URL"),
    ...
}

# openai_backend.py
def create_openai_model(model: str, api_key: str | None,
                        base_url: str | None = None,
                        api_version: str | None = None,
                        timeout: int = 30) -> ChatOpenAI | AzureChatOpenAI: ...

# ollama_backend.py
def create_ollama_model(model: str, api_key: str | None,
                        base_url: str | None = None,
                        timeout: int = 30) -> ChatOllama: ...

# _models.py
def _resolve_ollama_host(base_url: str | None) -> str | None: ...
def _check_ollama_daemon(api_key: str | None, base_url: str | None,
                         timeout: float = 5.0) -> dict[str, Any]: ...
def check_ollama_tool_capability(model: str, api_key: str | None,
                                 base_url: str | None,
                                 timeout: float = 5.0) -> dict[str, Any]: ...
def list_openai_models(api_key: str | None, base_url: str | None = None) -> list[str]: ...
def list_ollama_models(api_key: str | None, base_url: str | None = None) -> list[str]: ...

# _exceptions.py
def raise_connection_error(provider: str, env_var: str, original: Exception,
                           base_url_hint: str = "") -> NoReturn: ...

# verification.py
def _check_base_url_shape(base_url: str | None, api_version: str | None) -> dict[str, Any] | None: ...
def _list_models_for_backend(backend: str, api_key: str | None, base_url: str | None) -> dict[str, Any]: ...
```

## HOW

Integration points to change, in order:

1. `user_config.py:57` — key and env var.
2. `__init__.py:149` (`get_config_values` tuple), `:163` (returned dict key),
   `:141` (docstring), `:192` / `:218` (`_create_chat_model` kwargs).
3. Backend signatures. In `openai_backend.py` the SDK kwarg names stay as-is:
   `azure_endpoint=base_url` and `base_url=base_url`.
4. In `ollama_backend.py` the parameter becomes `base_url`; rename the local
   `base_url = _resolve_ollama_host(...)` to `resolved_url` to avoid shadowing.
5. `_preflight.py:40`, `_errors_404.py:25,82` — `config.get("base_url")`.
6. `verification.py` — function rename, result key `endpoint_shape` →
   `base_url_shape`, `error_type: "endpoint"` → `"base_url"`, and the hint string
   at `:343`.
7. `verify_formatting.py:113` — `"base_url_shape": "Base URL"` (Decision 19).
8. User-facing hint strings that spell "endpoint":
   `__init__.py:78,82,89`, `_exceptions.py:101` (`"base_url: {hint}"`),
   `_models.py:248` (`"base_url if using a custom server"`), `:345`
   (`"base_url/OLLAMA_HOST if not localhost"`), `verification.py:343`.

Grep for both `endpoint` and `ENDPOINT` (case-sensitive greps miss the env var).
Before renaming `error_type: "endpoint"`, grep tests for that literal.

## DATA

`_load_langchain_config()` returns the same flat `dict[str, str | None]`, with
key `"base_url"` in place of `"endpoint"`:

```python
{"default_provider": ..., "backend": ..., "model": ...,
 "api_key": ..., "base_url": ..., "api_version": ...}
```

## TDD

1. Add `tests/utils/test_user_config_schema.py` cases: `base_url` is in the
   `llm.langchain` schema with env var `MCP_CODER_LLM_LANGCHAIN_BASE_URL`, and
   `endpoint` is **not**.
2. Add a `_load_langchain_config` test: `MCP_CODER_LLM_LANGCHAIN_BASE_URL` set →
   returned under `"base_url"`; `MCP_CODER_LLM_LANGCHAIN_ENDPOINT` set → ignored.
3. Then rename throughout and update the existing test helpers until green.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
> Implement step 1: rename the langchain `endpoint` config key to `base_url`
> across source and tests, including the env var
> (`MCP_CODER_LLM_LANGCHAIN_ENDPOINT` → `MCP_CODER_LLM_LANGCHAIN_BASE_URL`), all
> backend/helper signatures, the user-facing hint strings, and the
> `endpoint_shape` result key / `"Endpoint"` label (→ `base_url_shape` /
> `"Base URL"`). There is **no alias** — `endpoint` is removed from the schema.
> Write the schema and loader tests first (TDD), then perform the rename.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
