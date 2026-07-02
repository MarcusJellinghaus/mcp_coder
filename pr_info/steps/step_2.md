# Step 2 — Part A2: `--check-models` live-probe 404 messaging

See `pr_info/steps/summary.md` for context. This step improves the wording of
the **opt-in** live `/models` probe (`mcp-coder verify --check-models`) so a 404
/ not-found reads as an endpoint/base-URL problem rather than a generic
"unknown" error. Auth and connection cases are already distinguished by the two
`except` clauses above; this adds the missing "path/endpoint" case.

This is a **pure reword**. The `--check-models` result is stored under
`available_models`, which is **excluded from `overall_ok` and
`_compute_exit_code`** — it only displays a "models" row and never affects
verify's exit code. What actually fails `verify` on a bad endpoint is the
separate unified "Reply with OK" test prompt in `execute_verify`, which this
step does **not** touch. Step 2 changes only the 404 message text.

## WHERE

- `src/mcp_coder/llm/providers/langchain/verification.py` — function
  `_list_models_for_backend`, generic `except Exception` branch only.
- `tests/llm/providers/langchain/test_langchain_verification.py` — unit test.

Do **not** touch `_models.py`.

## WHAT

Modify the final `except Exception as exc:` branch of `_list_models_for_backend`.
The signature and the `LLMConnectionError` / `LLMAuthError` branches stay
unchanged. Only the generic branch gains a 404 detection path.

## HOW (integration)

`_list_models_for_backend(backend, api_key, endpoint)` already receives
`endpoint`. Use it to gate the endpoint-oriented wording (a 404 without a custom
endpoint is more likely a genuine model-not-found, so keep it generic there).

## ALGORITHM (core logic)

Replace the body of the generic `except Exception as exc:` with:

```
msg = str(exc)
low = msg.lower()
if endpoint and ("404" in low or "not found" in low or "not_found" in low):
    return {"ok": False, "value": [],
            "error": f"{msg} — endpoint/base-URL likely wrong; use the base URL "
                     "e.g. …/v1 (mcp-coder appends /chat/completions)",
            "error_type": "endpoint"}
return {"ok": False, "value": [], "error": msg, "error_type": "unknown"}
```

Leave the `LLMConnectionError` (→ `"connection"`) and `LLMAuthError` (→ `"auth"`)
branches exactly as they are.

## DATA

Return shape is unchanged: `{"ok": bool, "value": list[str], "error": str,
"error_type": str}`. The new path sets `error_type="endpoint"` and appends the
base-URL guidance to `error`. The renderer (`_format_section`) shows `error`
in-line for `ok is False`, so no renderer change is needed.

## TESTS (write first)

Add to `test_langchain_verification.py`:

- Patch `_models.list_openai_models` to raise a generic `Exception("Error code:
  404 - {'detail': 'Not Found'}")`; call
  `_list_models_for_backend("openai", None, "https://h/v1/completions")`.
  Assert `ok is False`, `error_type == "endpoint"`, and the guidance ("base URL"
  / "/chat/completions") is present in `error`.
- Same 404 exception but `endpoint=None` → `error_type == "unknown"` (no
  endpoint wording), proving the gate.
- A non-404 generic exception (e.g. `Exception("boom")`) with an endpoint set →
  still `error_type == "unknown"` (only 404/not-found triggers the new path).

## LLM PROMPT

> Implement Step 2 from `pr_info/steps/step_2.md` (context in
> `pr_info/steps/summary.md`). Work test-first.
>
> 1. Add unit tests to
>    `tests/llm/providers/langchain/test_langchain_verification.py` for the
>    `_list_models_for_backend` generic-exception branch: a 404 with a custom
>    `endpoint` yields `error_type="endpoint"` and base-URL guidance in `error`;
>    a 404 with `endpoint=None`, and a non-404 error, both stay `"unknown"`.
> 2. In `src/mcp_coder/llm/providers/langchain/verification.py`, update only the
>    final `except Exception as exc:` branch of `_list_models_for_backend` per
>    the ALGORITHM. Leave the `LLMConnectionError` and `LLMAuthError` branches
>    and the function signature unchanged. Do not modify `_models.py`.
>
> Use MCP file tools only. After editing, run `run_pylint_check`,
> `run_pytest_check` (fast `-n auto` + `not …integration` exclusions), and
> `run_mypy_check`; fix any issues. This is one commit.
