# Plan Decisions Log

## Round 1 plan review (2026-05-12)

Changes applied to `pr_info/steps/*.md` based on the supervisor-approved
review of the initial plan for issue #727 (Add Ollama backend to
LangChain provider).

### Critical changes

- **C1 — step_5.md, pre-flight ordering and stream test:**
  - `_ollama_preflight(config)` must be called AFTER
    `_check_agent_dependencies()` but BEFORE `_create_chat_model(config)`
    / agent construction. Rationale: an Ollama-configured user without
    `langgraph` installed should still get the actionable "install
    langgraph" `ImportError`, not a tool-capability error.
  - For `_ask_agent_stream`: keep the generator semantics (the
    `ValueError` propagates when iteration begins). Do NOT refactor to
    eager-raise. No eager wrapper is needed.
  - Stream test asserts no thread is started: patch `threading.Thread`
    and assert it was NOT called when the generator is iterated and
    raises.

- **C2 — step_3.md, optional `api_key` rewrite:**
  - After the existing `_resolve_api_key(backend, config_api_key)`
    call, branch on `backend == "ollama" and api_key is None`.
  - In that branch, REPLACE `result["api_key"]` with
    `{"ok": True, "value": "not set (optional)", "source": None}`
    (preserves the existing schema with `source`).
  - This branch does NOT push `overall_ok` to `False` for Ollama.
  - If `OLLAMA_API_KEY` IS set, the normal masked-display path runs
    unchanged.

### Polish changes

- **P1 — step_1.md:** added
  `tests/llm/providers/langchain/test_langchain_provider.py` to the
  WHERE Modify list (the dispatch test for `_create_chat_model({
  "backend": "ollama", ...})` lives there).

- **P2 — step_2.md:** updated the NOT_FOUND test wording — add the new
  `"model 'foo' not found"` case as an additional parametrize case to
  the existing test at `test_langchain_provider.py:262`
  (`test_404_error_raises_value_error_with_model_hint`), not as a new
  standalone test. Added the provider test file to the WHERE Modify
  list.

- **P4 — step_3.md:** strengthened the daemon-probe note — if
  `ollama.Client`'s `headers` kwarg is not supported by the SDK, the
  probe must still work. Added a test note to cover the
  SDK-without-`headers`-kwarg path or for the helper to fall back
  gracefully.

- **P5 — step_4.md:** strengthened the
  `test_returns_not_ok_when_tools_missing` test — assert the error
  message MUST NOT contain a specific model name suggestion (e.g.
  `assert "llama" not in result["value"].lower()` and `assert "qwen"
  not in result["value"].lower()`).

- **P6 — step_5.md alignment:** clarified that `_ollama_preflight` is a
  **private helper inline in `__init__.py`** — no new module.

- **P8 — step_6.md:** replaced the
  `mcp-coder check file-size --max-lines 750` reference with the
  canonical `mcp__mcp-workspace__check_file_size` MCP tool.

### Explicitly NOT changed

- **Q1 (empty-string `OLLAMA_API_KEY` test):** skipped — existing
  `_resolve_api_key` already handles `""` as "not set" via truthiness.
- **Q2 (daemon probe retry):** skipped — single probe per
  planning_principles.md (no speculative robustness).
- **Q3 (capability check caching):** skipped — one HTTP round-trip on
  a local daemon is fine.
- **S1, S2, S3:** out of scope (placement of `_resolve_ollama_host`,
  dispatch table refactor, NOT_FOUND cleanup details).
- **P3, P7:** observations only, no action needed.
