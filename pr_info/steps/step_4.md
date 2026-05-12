# Step 4 — Tool capability helper + verify wiring

This step adds the shared `check_ollama_tool_capability()` helper that
probes `/api/show?name={model}` via the `ollama` Python client and
inspects `capabilities` for `"tools"`. It is wired into
`verify_langchain` so `mcp-coder verify` reports whether agent mode
will work for the configured model. Step 5 wires the same helper into
the agent pre-flight check.

## WHERE

**Modify:**
- `src/mcp_coder/llm/providers/langchain/_models.py` — add
  `check_ollama_tool_capability()`.
- `src/mcp_coder/llm/providers/langchain/verification.py`:
  - When `backend == "ollama"` AND a model is configured, call the
    helper and store the result under `"ollama_tools_capability"`.
  - Update `overall_ok` to AND in
    `ollama_tools_capability["ok"]` for `backend == "ollama"`.
- `src/mcp_coder/cli/commands/verify.py` — add
  `"ollama_tools_capability": "Tool-calling capability"` to
  `_LABEL_MAP`.
- `tests/llm/providers/langchain/test_langchain_models.py` — add
  `TestCheckOllamaToolCapability` class.
- `tests/llm/providers/langchain/test_langchain_verification.py` —
  extend `TestVerifyLangchainOllama` with capability cases.

## WHAT

```python
# _models.py
def check_ollama_tool_capability(
    model: str,
    api_key: str | None,
    endpoint: str | None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Probe /api/show for the model's capabilities. Verify-style dict."""
```

## HOW

- Helper signature returns a verify-style dict `{"ok": bool, "value":
  str}`. **This is intentional**: the same dict is rendered by
  `_format_section()` in `verify.py` AND consumed by `_ask_agent` /
  `_ask_agent_stream` in Step 5 (`raise ValueError(result["value"])`
  when `not result["ok"]`). One signature, one wording, two callers.
- Wording must be generic — NO hardcoded "use X instead" model
  suggestions (they would rot).
- `verify_langchain()` gates `overall_ok` on
  `ollama_tools_capability["ok"]` only when `backend == "ollama"` AND
  a model is configured. When no model is configured the entry is
  omitted and the existing `model["ok"] is False` failure already
  blocks `overall_ok`.

## ALGORITHM

```
def check_ollama_tool_capability(model, api_key, endpoint, timeout=5.0):
    if not model:
        return {"ok": False, "value": "no model configured"}
    import ollama
    host = _resolve_ollama_host(endpoint) or "http://localhost:11434"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    try:
        client = ollama.Client(host=host, headers=headers, timeout=timeout)
        info = client.show(model=model)
        caps = info.get("capabilities") or []  # adjust accessor as needed
        if "tools" in caps:
            return {"ok": True, "value": f"model {model!r} supports tools"}
        return {"ok": False, "value":
            f"model {model!r} does not advertise the 'tools' capability — "
            "agent mode requires a tool-calling model"}
    except Exception as exc:  # narrow once SDK exception types are known
        return {"ok": False, "value":
            f"could not verify tool capability for {model!r}: {exc}"}
```

**Note on `client.show()` return shape:** verify against the
installed `ollama` library — newer versions may return a Pydantic
model where `info.capabilities` is a list attribute. Adjust accessor
accordingly. The "tools" substring check is library-agnostic.

## DATA

**Returns:** `dict[str, Any]` with `ok: bool`, `value: str`.

**`verify_langchain()` additions for `backend == "ollama"` AND
`model`:**
- `result["ollama_tools_capability"]` — dict above
- `result["overall_ok"]` — also requires
  `ollama_tools_capability["ok"]`

## Tests (write FIRST, TDD)

`tests/llm/providers/langchain/test_langchain_models.py` — new class
`TestCheckOllamaToolCapability`:

- `test_returns_ok_when_tools_in_capabilities` — mocked `show()`
  returns `{"capabilities": ["tools", "completion"]}` → `ok: True`.
- `test_returns_not_ok_when_tools_missing` — `{"capabilities":
  ["completion"]}` → `ok: False`, generic wording mentions `"tools"`
  but no specific model suggestion.
- `test_returns_not_ok_when_capabilities_empty` — `{}` → `ok: False`.
- `test_returns_not_ok_when_show_raises` — `show()` raises → `ok:
  False`, wording mentions the error.
- `test_returns_not_ok_when_model_is_empty_string` — `model=""` →
  `ok: False` without calling the network.
- `test_uses_normalized_host`
- `test_uses_default_host_when_no_endpoint`

`tests/llm/providers/langchain/test_langchain_verification.py` —
extend `TestVerifyLangchainOllama`:

- `test_ollama_capability_entry_present_when_model_configured`
- `test_ollama_capability_missing_fails_overall_ok`
- `test_ollama_capability_present_does_not_fail_overall_ok`
- `test_ollama_no_model_omits_capability_entry`

## Definition of done

- All new tests pass.
- Existing verify tests still pass.
- `mcp-coder verify` rendering for ollama shows the `Tool-calling
  capability` row.
- All three MCP code-quality checks pass.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement Step 4 only. Follow TDD: extend
tests/llm/providers/langchain/test_langchain_models.py with
TestCheckOllamaToolCapability and extend the Ollama verify test
class in test_langchain_verification.py with the four capability
cases FIRST, then implement check_ollama_tool_capability() in
_models.py and wire it into verify_langchain().

The helper MUST return the verify-style dict {"ok": bool, "value":
str} — Step 5 reuses it directly from the agent pre-flight check
(no second wording source).

Use generic error wording. Do NOT include any "use X instead"
model suggestions — that text would rot.

Add "ollama_tools_capability" → "Tool-calling capability" to
_LABEL_MAP in src/mcp_coder/cli/commands/verify.py.

overall_ok gates on capability only when backend == "ollama" AND a
model is configured. When model is not configured, omit the
capability entry; the existing model["ok"] is False already blocks
overall_ok.

Do NOT modify agent.py or _ask_agent / _ask_agent_stream in
__init__.py — that's Step 5.

After the edits, run all three MCP code-quality checks and confirm
zero issues before reporting the step complete.
```
