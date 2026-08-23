# Step 9 — Contract findings in `verify` + exit-code wiring

`verify` reports **every** violation at once (the validator is non-raising) and
required-missing feeds `overall_ok` → exit 1 with a named cause.

## WHERE

- `src/mcp_coder/llm/providers/langchain/verification.py` — `verify_langchain`
- `src/mcp_coder/cli/commands/verify_formatting.py` — two `_LABEL_MAP` entries
- `tests/llm/providers/langchain/test_langchain_verification.py`
- `tests/cli/commands/test_verify_exit_codes.py`

## WHAT

No new public function. `verify_langchain` gains:

```python
findings = {f["key"]: f for f in validate(config)}
```

and uses it to build the `model` / `api_key` rows and to add `base_url` /
`api_version` / `backend` rows.

## HOW

- Findings reuse the existing `{"ok", "value"}` entry shape, so
  `_format_section` renders them for free (`ok=None` → `[WARN]`) and
  `verify_exit_code.py` needs **no** change — everything flows through
  `overall_ok`.
- The contract **replaces** the naive rows rather than running beside them:
  - `result["model"]` — `ok`/`value` from the finding when present, else
    `{"ok": True, "value": model}`.
  - `result["api_key"]` — keep the masked value and `source` from
    `_resolve_api_key`; take `ok` from the finding when present. **Delete** the
    hand-rolled `backend == "ollama"` special case: the contract already declares
    `api_key` optional for ollama, so no finding is produced.
  - Remaining findings (`base_url`, `api_version`, `backend`) become their own
    rows.
- `_LABEL_MAP` additions: `"base_url": "Base URL"`, `"api_version": "API version"`.
  Note `base_url` and `base_url_shape` share the `"Base URL"` label but are
  **mutually exclusive by construction**: the shape check runs only for
  non-Azure `openai`, while contract `base_url` findings arise only in Azure mode
  or on non-openai backends.
- `overall_ok` composition gains one clause:
  ```python
  overall_ok = ... and all(f["ok"] is not False for f in findings.values())
  ```
  `ok=None` warnings (ignored keys, unauthenticated-relay `api_key`) stay
  exit-neutral.

## ALGORITHM

```
findings = {f["key"]: f for f in validate(config)}
result["model"]   = _row_from(findings.get("model"),   default_ok=True, default_value=model)
key, src          = _resolve_api_key(backend, config_api_key)
result["api_key"] = {**_row_from(findings.get("api_key"), True, _mask_api_key(key)), "source": src}
for k, f in findings.items():
    result.setdefault(k, {"ok": f["ok"], "value": f["value"]})
overall_ok = <existing clauses> and all(f["ok"] is not False for f in findings.values())
```

## DATA

```
=== LLM PROVIDER DETAILS ==================================================
  Backend               [OK]   openai
  Model                 [OK]   Qwen-2.5-72B
  API key               [WARN] no api_key and no OPENAI_API_KEY — fine if the server at base_url is unauthenticated
  API version           [WARN] api_version is ignored by backend 'gemini' — remove it
```

## TDD

1. Azure mode without `base_url` → `result["base_url"]["ok"] is False` and
   `overall_ok is False`; the message names `api_version`.
2. Public OpenAI without any key → `api_key` `ok=False`, `overall_ok is False`.
3. `base_url` set, no key → `api_key` `ok=None`, `overall_ok` **unchanged**.
4. `gemini` + `base_url` → an `[WARN]` row, `overall_ok` unchanged.
5. `ollama` with no key → `api_key` `ok=True` (special case removed, behaviour
   preserved).
6. Multiple violations → **all** are present in the result (nothing dies on the
   first).
7. Exit code: case 1 yields exit 1 from `execute_verify`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_9.md`.
> Implement step 9: call the step-5 `validate()` from `verify_langchain`, merge
> the findings into the result dict (replacing the naive `model` / `api_key` rows
> and deleting the hand-rolled ollama api_key special case), add the two
> `_LABEL_MAP` entries, and extend `overall_ok` so `ok is False` findings cause
> exit 1 while `ok is None` warnings stay exit-neutral. Do not modify
> `verify_exit_code.py`. `verify` must report every violation, not just the
> first. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
