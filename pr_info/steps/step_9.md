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

mode = mode_of(config)
findings = {f["key"]: f for f in validate(config)}
scoped = mode is not None
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
  - `result["api_key"]` — when a finding exists, **both** `ok` and `value` come
    from it, so the row shows the actionable contract message (naming `api_key`
    and the backend's env vars) rather than a bare `not set`; the acceptance
    criterion is "exit 1, **naming the contract violation**", and a masked-value
    row cannot name it. When there is no finding, the value is the masked key
    from `_resolve_api_key`. `source` (3-tuple after step 7) is carried through
    in both branches. **Delete** the hand-rolled `backend == "ollama"` special case: the
    contract already declares `api_key` optional for ollama, so no finding is
    produced. **Keep its value text**: with no key resolved, `_mask_api_key`
    returns `None` and `_format_section` stringifies that to the literal
    `"None"` (`verify_formatting.py:194`). The fallback must therefore never be
    a bare `_mask_api_key(key)`; `"not set (optional)"` keeps the row reading
    exactly as it does today for ollama, and for any other backend whose
    `api_key` is optional and unset.
    **But `"not set (optional)"` is only true when nothing supplied a key.**
    After step 7 re-keys `_resolve_api_key` on the **mode**, an Azure key in
    `AZURE_OPENAI_API_KEY` or a gemini key in `GOOGLE_API_KEY` resolves normally
    and this branch renders the masked value. The one remaining no-key,
    no-finding case is gemini's keyless Vertex carve-out, where
    `_resolve_api_key` returns a `source` with a `None` key; that renders
    `f"satisfied via {source}"`, never `"not set (optional)"` — `api_key` is
    `required` for gemini, so calling it optional would be a second false claim.
    Pass `mode`, not `backend`, to `_resolve_api_key`.
  - **"No finding" only means "satisfied" when the contract could be applied.**
    When `mode_of(config)` returns `None` — an unset `backend`, or a typo like
    `opnai` — `validate()` short-circuits and emits *only* the `backend`
    finding, so it says nothing at all about `model` or `api_key`. Defaulting
    those rows to `ok=True` there would render `Model [OK] None` and
    `API key [OK] not set (optional)` for a config that has neither, where both
    are `[ERR]` today: a diagnosability regression in the one PR that exists to
    remove them. So the defaults are **contract-aware**:
    - mode resolvable → `default_ok=True` (the contract checked the field and
      raised nothing), value `model` / `_api_key_default_value()` (ALGORITHM);
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
  `ok=None` warnings (ignored keys) stay exit-neutral.

## ALGORITHM

```
mode     = mode_of(config)
findings = {f["key"]: f for f in validate(config)}
scoped   = mode is not None                  # False -> contract said nothing
                                             #          about model / api_key
key, src, _over = _resolve_api_key(mode, config_api_key)   # mode, not backend

def _api_key_default_value():
    if key is not None:      return _mask_api_key(key)
    if src is not None:      return f"satisfied via {src}"   # keyless carve-out
    return "not set (optional)" if scoped else "not set"

result["model"]   = _row_from(findings.get("model"),
                              default_ok=True if scoped else model is not None,
                              default_value=model)
result["api_key"] = {**_row_from(findings.get("api_key"),
                                 default_ok=True if scoped else key is not None,
                                 default_value=_api_key_default_value()),
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
  API key               [ERR]  no api_key in [llm.langchain] and no OPENAI_API_KEY — set one; the OpenAI client cannot be built without credentials, even against a custom base_url
  API version           [WARN] api_version is ignored by backend 'gemini' — remove it
```

## TDD

1. Azure mode without `base_url` → `result["base_url"]["ok"] is False` and
   `overall_ok is False`; the message names `api_version`.
2. Public OpenAI without any key → `api_key` `ok=False`, `overall_ok is False`,
   **and** `result["api_key"]["value"]` is the finding's message — assert it
   names both `api_key` and `OPENAI_API_KEY`, and that it is not `"not set"` /
   `"not set (optional)"` / `"None"`. Assert the rendered row too: the finding
   branch is the whole point of the acceptance criterion.
2b. The no-finding branch renders the key, not a message: `openai` with a
   resolved key → `api_key` `ok=True`, `value == _mask_api_key(key)` and
   `source` is set. Together with case 2 this pins both branches.
3. `base_url` set, no key → `api_key` `ok=False`, `overall_ok is False` and the
   same finding message in `value` (no `base_url` exception — see step 5: the
   client cannot be constructed without credentials).
4. `gemini` + `base_url` → an `[WARN]` row, `overall_ok` unchanged.
5. `ollama` with no key → `api_key` `ok=True` **and** `value == "not set
   (optional)"` (special case removed, rendered text preserved); assert the
   rendered row too, so the `_mask_api_key(None)` → literal `"None"` regression
   cannot slip through.
5b. `"not set (optional)"` never appears on a `required` api_key row. All
   credential vars cleared, then: Azure mode with only `AZURE_OPENAI_API_KEY` →
   `ok=True`, `value == _mask_api_key(key)`, `source == "AZURE_OPENAI_API_KEY env
   var"`; `gemini` with only `GOOGLE_API_KEY` → same shape; `gemini` with only
   `GOOGLE_GENAI_USE_VERTEXAI` → `ok=True` and
   `value == "satisfied via GOOGLE_GENAI_USE_VERTEXAI env var"`. Assert the
   rendered rows in all three.
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
> the findings into the result dict — when a finding exists for a key, **both**
> its `ok` and its `value` win, so the `API key` row shows the contract message
> naming `api_key`/`OPENAI_API_KEY` rather than a bare `not set`; only the
> no-finding branch shows the masked key. This replaces the naive
> `model` / `api_key` rows,
> deleting the hand-rolled ollama api_key special case while keeping its
> `"not set (optional)"` text for a genuinely optional-and-unset key. Pass
> `mode_of(config)` — not `backend` — to step 7's mode-keyed `_resolve_api_key`,
> and render `f"satisfied via {source}"` when it reports a source with no
> readable key (gemini's keyless Vertex carve-out): `[OK] not set (optional)` on
> a `required` api_key row is a false claim. **Overwrite** the pre-populated `backend`
> row when a `backend` finding exists so an unsupported backend is explained
> rather than silently exiting 1. Make the `model` / `api_key` defaults
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
