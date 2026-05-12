# Issue #727 — Add Ollama backend to LangChain provider

Native Ollama backend for the LangChain provider, mirroring the shape of the
existing `openai_backend.py` / `gemini_backend.py` / `anthropic_backend.py`.
The `[langchain-ollama]` extra and `langchain-ollama>=0.2.0` wrapper are
already declared (from #829) — this PR lands the backend code, model
listing, verification, tool-calling capability check, agent integration,
tests, and docs.

## Architectural / design changes

This PR follows the established four-sibling pattern for backends, with
three Ollama-specific knobs that diverge from the other backends:

1. **`OLLAMA_HOST` is `host:port`, not a URL.** A single shared helper
   `_resolve_ollama_host(endpoint)` in `_models.py` does
   env > config > None resolution AND prepends `http://` when no scheme is
   present. Reused by the backend factory, model listing, daemon probe,
   and capability check.

2. **`api_key` is optional for Ollama.** Plain localhost has no auth, so
   `verify` reports a missing key as `"not set (optional)"` and the
   missing key does not fail `overall_ok`. The parameter shape stays
   identical to the other three backends so the signatures stay
   symmetric.

3. **Tool-calling support is per-model and probed at startup.** A shared
   helper `check_ollama_tool_capability(model, api_key, endpoint)`
   queries `/api/show?name={model}` via the `ollama` Python client and
   inspects `capabilities` for `"tools"`. Called from both
   `verify_langchain` (so `mcp-coder verify` reflects whether agent mode
   is usable) and from `_ask_agent` / `_ask_agent_stream` in
   `__init__.py` (pre-flight, before `create_react_agent`). The helper
   returns the verify-style dict `{"ok": bool, "value": str}` so both
   call sites share one error wording. **The agent pre-flight lives in
   `__init__.py`, not `agent.py`, so `agent.py` stays
   backend-agnostic.**

Beyond these three, the implementation is symmetric with the existing
backends:

- `create_ollama_model()` mirrors `create_anthropic_model()` in shape.
- `list_ollama_models()` mirrors `list_anthropic_models()` and uses the
  vendor SDK (`ollama` Python client, transitively installed via
  `langchain-ollama`).
- Verification additions slot into the same dict-result, label-mapped
  formatter machinery used for every other provider.
- `overall_ok` gating for Ollama adds two new clauses
  (`ollama_daemon["ok"] AND ollama_tools_capability["ok"]`) alongside
  the existing `backend / backend_package / mcp_adapters / langgraph`
  checks.

### `pyproject.toml` — no change

The `[langchain-ollama]` extra and `langchain-ollama>=0.2.0` dependency
already exist from #829.

### Files created

```
src/mcp_coder/llm/providers/langchain/ollama_backend.py
tests/llm/providers/langchain/test_langchain_ollama.py
tests/llm/providers/langchain/test_langchain_ollama_agent.py
```

### Files modified

```
src/mcp_coder/llm/providers/langchain/__init__.py
src/mcp_coder/llm/providers/langchain/_models.py
src/mcp_coder/llm/providers/langchain/verification.py
src/mcp_coder/cli/commands/verify.py            (_LABEL_MAP additions only)
tests/llm/providers/langchain/conftest.py        (mock langchain_ollama + ollama)
tests/llm/providers/langchain/test_langchain_models.py
tests/llm/providers/langchain/test_langchain_verification.py
docs/configuration/config.md
docs/configuration/optional-dependencies.md
```

## Steps

1. **Backend factory + dispatch wiring + conftest mocks** —
   `create_ollama_model()`, `_resolve_ollama_host()`, hook into
   `_create_chat_model()` and `_BACKEND_ERROR_PARAMS`.
2. **Model listing + NOT_FOUND substring extension** —
   `list_ollama_models()` via the `ollama` Python client, wired into
   `_get_model_suggestions`; extend the NOT_FOUND match in `_ask_text`
   and `_ask_text_stream`.
3. **Daemon reachability probe + verify wiring** —
   `_check_ollama_daemon()`, `_BACKEND_ENV_VARS` / `_BACKEND_PACKAGES`
   entries, `ollama_daemon` result entry with 401/403-vs-refused
   distinction, optional `api_key` handling, `_list_models_for_backend`
   ollama branch, `_LABEL_MAP` additions, `overall_ok` daemon gating.
4. **Tool capability helper + verify wiring** —
   `check_ollama_tool_capability()`, `ollama_tools_capability` result
   entry, `_LABEL_MAP` addition, `overall_ok` capability gating.
5. **Agent pre-flight capability check** — call the shared helper from
   `_ask_agent` and `_ask_agent_stream` before invoking the agent;
   raise a clear error when capability is missing.
6. **Documentation updates** — replace the OpenAI-compatible Ollama
   example in `config.md` with a native `backend = "ollama"` example;
   drop the "backend integration in progress" qualifier from
   `optional-dependencies.md`.
