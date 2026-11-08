# Step 1 — Key-order test for `verify_langchain` (before any change)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
> Add the key-order test described below. Do **not** change production code.
> The test must pass against today's code. Run pylint, pytest, mypy, format, then
> commit as one commit.

## Why

`mcp-coder verify` prints rows in dict insertion order, and install hints follow
that order. Step 5 splits `verify_langchain`; this test pins the order now so it
can prove the split changed nothing. It patches **only targets that do not move**:
`verification._load_langchain_config`, `_models.*`, `ollama_backend.*`.
Never patch `verification._check_package_installed` (it moves in step 5); the
package rows exist whether a package is installed or not, so the key order does
not depend on the environment.

## WHERE

New file `tests/llm/providers/langchain/test_langchain_verify_row_order.py`.

## WHAT

```python
_VERIFICATION = "mcp_coder.llm.providers.langchain.verification"
_MODELS = "mcp_coder.llm.providers.langchain._models"
_OLLAMA = "mcp_coder.llm.providers.langchain.ollama_backend"

def test_row_order_ollama_with_probe_rows(monkeypatch: pytest.MonkeyPatch) -> None: ...
def test_row_order_without_probe_rows() -> None: ...
```

## HOW

Test 1 – ollama, every optional row present:
- `pytest.importorskip("langchain_ollama")` (patching `ollama_backend.*` imports it).
- `monkeypatch.setenv("OLLAMA_HOST", "http://box:11434")`,
  `monkeypatch.setenv("OLLAMA_API_KEY", "env-key-12345678")`.
- config: `{"default_provider": None, "backend": "ollama", "model": "llama3",
  "api_key": "cfg-key-12345678", "base_url": None, "api_version": None}`
  (the config `api_key` is needed for the `api_key_override` row).
- patch `f"{_OLLAMA}.create_ollama_model"` with
  `return_value=SimpleNamespace(base_url="http://box:11434")` — a real string,
  not a `MagicMock` (a mock makes `dialed_url` return a mock and the redirect row
  disappears).
- patch `f"{_MODELS}._check_ollama_daemon"` and
  `f"{_MODELS}.check_ollama_tool_capability"` → `{"ok": True, "value": "ok"}`;
  `f"{_MODELS}.list_ollama_models"` → `["llama3"]`.
- call `verify_langchain(check_models=True)`.

Test 2 – no probe rows (MCP rows sit directly before `overall_ok`):
- config: backend `"gemini"`, model `"gemini-2.5-flash"`, `api_key`
  `"cfg-key-12345678"`, all else None; `check_models=False`.
  Gemini is not a targeted backend, so `resolve_target` builds no client.
- Clear `GEMINI_API_KEY` / `GOOGLE_API_KEY` / `GOOGLE_GENAI_USE_VERTEXAI` with
  `monkeypatch.delenv(..., raising=False)`.

## DATA

Assert `list(result)` equals exactly:

Test 1:
```python
["backend", "model", "api_key", "effective_config", "langchain_core",
 "backend_package", "base_url_redirect", "api_key_override",
 "mcp_adapters", "langgraph",
 "ollama_daemon", "ollama_tools_capability", "available_models", "model_check",
 "overall_ok"]
```
Test 2:
```python
["backend", "model", "api_key", "effective_config", "langchain_core",
 "backend_package", "mcp_adapters", "langgraph", "overall_ok"]
```

These lists are derived from reading today's `verify_langchain`. If the real
order on unchanged code differs (e.g. an extra finding row), pin the order the
current code actually produces — the test records today's behaviour; it does not
define new behaviour. Also assert `"base_url_redirect"` and `"api_key_override"`
are present in test 1, so a silently missing row cannot pass.
