# Step 3 — Daemon reachability probe + verify wiring

This step adds the local-Ollama-daemon reachability probe to
`verify_langchain()` for `backend == "ollama"`, plumbs Ollama through
the verify infrastructure (env-var map, package map, optional
`api_key` handling, `_list_models_for_backend` was already done in
Step 2), and adds the `_LABEL_MAP` entry so the verify CLI renders the
new section. Tool-capability check is Step 4.

## WHERE

**Modify:**
- `src/mcp_coder/llm/providers/langchain/_models.py` — add
  `_check_ollama_daemon()`.
- `src/mcp_coder/llm/providers/langchain/verification.py`:
  - Extend `_BACKEND_ENV_VARS` and `_BACKEND_PACKAGES` with `"ollama"`.
  - In `verify_langchain()`, treat Ollama's `api_key` as optional
    (missing → `"not set (optional)"`, `ok: True`).
  - When `backend == "ollama"`, call `_check_ollama_daemon()` and add
    its result under the `"ollama_daemon"` key.
  - Update `overall_ok` to include `ollama_daemon["ok"]` for
    `backend == "ollama"`.
- `src/mcp_coder/cli/commands/verify.py` — add `"ollama_daemon":
  "Local Ollama daemon"` to `_LABEL_MAP`.
- `tests/llm/providers/langchain/test_langchain_verification.py` —
  add `TestVerifyLangchainOllama` class.

## WHAT

```python
# _models.py
def _check_ollama_daemon(
    api_key: str | None,
    endpoint: str | None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Probe the local Ollama daemon. Returns verify-style dict."""
```

## HOW

- `_check_ollama_daemon()` calls `ollama.Client(host=..., timeout=...)`
  and invokes `.list()` (hits `/api/tags`).
- Outcomes:
  - 200 → `{"ok": True, "value": "local Ollama daemon reachable at
    <url>"}`.
  - 401 / 403 (proxy auth required) → `{"ok": False, "value": "local
    Ollama daemon reachable but auth required — set OLLAMA_API_KEY or
    api_key in config.toml"}`.
  - Connection refused / timeout / DNS failure → `{"ok": False,
    "value": "local Ollama daemon not reachable — is `ollama serve`
    running?"}`.
- The 401/403 vs connection-error distinction is made by inspecting
  the `ollama` library's exception type and status code. Most likely
  `ollama.ResponseError` exposes `.status_code`; fall back to
  string-sniffing the exception message for `"401"` / `"403"` if the
  attribute is unavailable.
- `verify_langchain()`:
  - Resolves `api_key` as before, but for `backend == "ollama"` sets
    `result["api_key"] = {"ok": True, "value": "not set (optional)"}`
    when no key is found anywhere.
  - When `backend == "ollama"`: `result["ollama_daemon"] =
    _check_ollama_daemon(api_key, endpoint)`.
  - Updates `overall_ok` to AND in `result["ollama_daemon"]["ok"]`
    when `backend == "ollama"`. Capability gate comes in Step 4.

## ALGORITHM

```
def _check_ollama_daemon(api_key, endpoint, timeout=5.0):
    import ollama
    host = _resolve_ollama_host(endpoint) or "http://localhost:11434"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    try:
        client = ollama.Client(host=host, headers=headers, timeout=timeout)
        client.list()
        return {"ok": True, "value": f"reachable at {host}"}
    except ollama.ResponseError as exc:
        if getattr(exc, "status_code", None) in (401, 403):
            return {"ok": False, "value": "...auth required..."}
        return {"ok": False, "value": "...not reachable..."}
    except CONNECTION_ERRORS + (TimeoutError,) as exc:
        return {"ok": False, "value": "...not reachable..."}
```

**Note on `ollama.Client` constructor:** verify which kwargs are
supported (`headers`, `timeout`). If `headers` is not supported, drop
the proxy-auth header on the probe call and rely on connection-error
detection only — the probe should always do something useful, even
when the SDK API is leaner than expected.

## DATA

**`_check_ollama_daemon` returns:** `dict[str, Any]` with keys:
- `ok: bool`
- `value: str` — user-facing wording chosen by outcome bucket above.

**`verify_langchain()` additions for `backend == "ollama"`:**
- `result["ollama_daemon"]` — dict above
- `result["api_key"]` — `{"ok": True, "value": "not set (optional)"}`
  when no key found, otherwise unchanged
- `result["overall_ok"]` — also requires `ollama_daemon["ok"]`

## Tests (write FIRST, TDD)

`tests/llm/providers/langchain/test_langchain_verification.py` —
new class `TestVerifyLangchainOllama`:

- `test_ollama_no_api_key_is_optional` — config has `backend="ollama"`,
  no key anywhere → `result["api_key"]["ok"] is True` AND
  `result["api_key"]["value"] == "not set (optional)"` AND
  `result["overall_ok"]` not failed because of api_key.
- `test_ollama_with_api_key_works_as_before` — key present → masked
  value displayed, `ok: True`.
- `test_ollama_daemon_reachable` — mock `_check_ollama_daemon` to
  return `{"ok": True, ...}` → `result["ollama_daemon"]["ok"] is
  True` AND `overall_ok` not affected negatively.
- `test_ollama_daemon_unreachable_fails_overall` — mock returns
  `{"ok": False, ...}` (connection refused wording) → `overall_ok
  is False`.
- `test_ollama_daemon_auth_required_fails_overall` — mock returns
  `{"ok": False, "value": "...auth required..."}` →
  `overall_ok is False`.
- `test_non_ollama_backend_has_no_ollama_daemon_entry` —
  `backend="openai"` → `"ollama_daemon"` not in result.

New class `TestCheckOllamaDaemon` for `_check_ollama_daemon` itself
(in `test_langchain_models.py`):
- `test_returns_ok_when_list_succeeds`
- `test_returns_auth_required_on_401`
- `test_returns_auth_required_on_403`
- `test_returns_unreachable_on_connection_error`
- `test_uses_default_host_when_neither_env_nor_endpoint_set`
- `test_uses_normalized_host_from_endpoint`

## Definition of done

- All new tests pass.
- Existing verify tests still pass (no regression in openai / gemini /
  anthropic paths).
- `mcp-coder verify` rendering for an `ollama`-configured user shows
  the `Local Ollama daemon` row (verified visually if possible, or
  via a rendering test).
- All three MCP code-quality checks pass.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement Step 3 only. Follow TDD: extend
tests/llm/providers/langchain/test_langchain_models.py with
TestCheckOllamaDaemon and
tests/llm/providers/langchain/test_langchain_verification.py with
TestVerifyLangchainOllama FIRST, then implement the daemon probe and
the verify-wiring changes described in the step.

Treat api_key as optional ONLY for backend == "ollama" — every other
backend's behavior must stay unchanged.

Add "ollama_daemon" → "Local Ollama daemon" to _LABEL_MAP in
src/mcp_coder/cli/commands/verify.py so the existing
_format_section() loop renders the new entry without any formatter
changes.

Verify the actual ollama-python exception types (ollama.ResponseError
and friends) for the 401/403 vs connection-error split. If
status_code isn't exposed, fall back to substring-sniffing the
exception message for "401" / "403"; otherwise rely on
CONNECTION_ERRORS catch.

Do NOT add the tool-capability check yet — that is Step 4. The
overall_ok gating in this step covers daemon reachability only.

After the edits, run all three MCP code-quality checks and confirm
zero issues before reporting the step complete.
```
