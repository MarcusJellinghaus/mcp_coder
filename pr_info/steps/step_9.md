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
from ._config_diagnostics import mode_of, validate

findings = {f["key"]: f for f in validate(config)}
scoped = mode_of(config) is not None
```

and uses it to build the `model` / `api_key` rows and to add `base_url` /
`api_version` / `backend` rows.

## HOW

- Findings reuse the existing `{"ok", "value"}` entry shape, so
  `_format_section` renders them for free (`ok=None` → `[WARN]`) and
  `verify_exit_code.py` needs **no** change — everything flows through
  `overall_ok`.
- The contract **replaces** the naive rows rather than running beside them:
  - `result["model"]` — `ok`/`value` from the finding when present, else the
    contract-aware default below.
  - `result["api_key"]` — keep the masked value and `source` from
    `_resolve_api_key` (3-tuple after step 7); take `ok` from the finding when
    present. **Delete** the hand-rolled `backend == "ollama"` special case: the
    contract already declares `api_key` optional for ollama, so no finding is
    produced. **Keep its value text**: with no key resolved, `_mask_api_key`
    returns `None` and `_format_section` stringifies that to the literal
    `"None"` (`verify_formatting.py:194`). The fallback value must therefore be
    `_mask_api_key(key) or "not set (optional)"` — the row reads exactly as it
    does today for ollama, and for any other backend whose `api_key` is optional
    and unset.
  - **"No finding" only means "satisfied" when the contract could be applied.**
    When `mode_of(config)` returns `None` — an unset `backend`, or a typo like
    `opnai` — `validate()` short-circuits and emits *only* the `backend`
    finding, so it says nothing at all about `model` or `api_key`. Defaulting
    those rows to `ok=True` there would render `Model [OK] None` and
    `API key [OK] not set (optional)` for a config that has neither, where both
    are `[ERR]` today: a diagnosability regression in the one PR that exists to
    remove them. So the defaults are **contract-aware**:
    - mode resolvable → `default_ok=True` (the contract checked the field and
      raised nothing), value `model` / `_mask_api_key(key) or "not set (optional)"`;
    - mode `None` → fall back to today's presence test, `model is not None` /
      `key is not None`, with the unset text `"not set"` (not
      `"not set (optional)"` — nothing has established that it is optional).
  - `result["backend"]` — **overwrite, do not `setdefault`.** The key is already
    populated at `verification.py:199` with `{"ok": backend is not None, ...}`,
    so an unsupported backend name would otherwise render `Backend [OK] opnai`
    while `overall_ok` is False — exit 1 with no visible cause. When a `backend`
    finding exists, its `ok`/`value` replace that entry (value = the
    contract-violation message naming the supported backends); otherwise the
    existing entry stands.
  - Remaining findings (`base_url`, `api_version`) become their own rows via
    `setdefault`, which is safe because those keys are not pre-populated.
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
scoped   = mode_of(config) is not None       # False -> contract said nothing
                                             #          about model / api_key
key, src, _over = _resolve_api_key(backend, config_api_key)

result["model"]   = _row_from(findings.get("model"),
                              default_ok=True if scoped else model is not None,
                              default_value=model)
result["api_key"] = {**_row_from(findings.get("api_key"),
                                 default_ok=True if scoped else key is not None,
                                 default_value=_mask_api_key(key)
                                     or ("not set (optional)" if scoped else "not set")),
                     "source": src}
if "backend" in findings:                       # overwrite: the key already exists
    result["backend"] = {"ok": findings["backend"]["ok"],
                         "value": findings["backend"]["value"]}
for k, f in findings.items():                   # base_url / api_version
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
5. `ollama` with no key → `api_key` `ok=True` **and** `value == "not set
   (optional)"` (special case removed, rendered text preserved); assert the
   rendered row too, so the `_mask_api_key(None)` → literal `"None"` regression
   cannot slip through.
6. Multiple violations → **all** are present in the result (nothing dies on the
   first).
7. Exit code: case 1 yields exit 1 from `execute_verify`.
8. Unsupported backend (`backend = "opnai"`) → `result["backend"]["ok"] is
   False` and its value is the contract message listing the supported backends
   (the pre-populated `[OK] opnai` row is **replaced**, not kept), and
   `overall_ok is False`.
8b. Unsupported backend **with neither `model` nor `api_key` set** (and no
   backend env var) → `result["model"]["ok"] is False` and
   `result["api_key"]["ok"] is False`; the api_key value is `"not set"`, **not**
   `"not set (optional)"`. Assert the rendered rows as well: no `[OK]` may
   appear for a field the contract never got to check. Same assertion for
   `backend` entirely unset.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_9.md`.
> Implement step 9: call the step-5 `validate()` from `verify_langchain`, merge
> the findings into the result dict (replacing the naive `model` / `api_key` rows
> and deleting the hand-rolled ollama api_key special case while keeping its
> `"not set (optional)"` text, and **overwriting** the pre-populated `backend`
> row when a `backend` finding exists so an unsupported backend is explained
> rather than silently exiting 1). Make the `model` / `api_key` defaults
> **contract-aware**: `validate()` short-circuits when `mode_of(config)` is
> `None`, so "no finding" there does not mean "satisfied" — fall back to today's
> presence test (`model is not None`, `key is not None`) and the plain
> `"not set"` text, so a typo'd or unset `backend` never renders
> `Model [OK] None` / `API key [OK] not set (optional)`. Add the two
> `_LABEL_MAP` entries, and extend `overall_ok` so `ok is False` findings cause
> exit 1 while `ok is None` warnings stay exit-neutral. Do not modify
> `verify_exit_code.py`. `verify` must report every violation, not just the
> first. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
