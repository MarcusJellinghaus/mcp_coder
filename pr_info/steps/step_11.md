# Step 11 — `--check-models` cross-checks the configured model

`verify` checks only that `model` is non-empty, and `--check-models` merely
*lists* models without comparing the configured one — so a wrong model name
passes `verify` and fails at prompt time.

## WHERE

- `src/mcp_coder/llm/providers/langchain/verification.py`
- `src/mcp_coder/cli/commands/verify_formatting.py` — one `_LABEL_MAP` entry
- `tests/llm/providers/langchain/test_langchain_verification.py`

## WHAT

```python
def _check_model_listed(
    model: str | None, listing: dict[str, Any]
) -> dict[str, Any]:
    """Cross-check the configured model against a model listing."""
```

## HOW

- Runs only under `check_models` (the listing is a network call), immediately
  after `result["available_models"]` is populated, as `result["model_check"]`.
- Reuses `utils.config_hints.suggest()` from step 2 for near-misses — one
  near-miss implementation for the whole project.
- **Degrade gracefully**: some LiteLLM proxies return auth errors or 404 on
  `/models`. When `listing["ok"]` is falsy, report `ok=None` with
  `"could not verify (server does not expose /models)"` — never an error.
- Advisory only: `ok` is `True` or `None`, never `False`, so `overall_ok` is
  untouched. A genuinely wrong model still fails the live test prompt, which
  already sets exit 1.
- `_LABEL_MAP` entry: `"model_check": "Model available"`.

## ALGORITHM

```
_check_model_listed(model, listing):
    if not listing.get("ok"): return {"ok": None, "value": "could not verify (server does not expose /models)"}
    names = listing.get("value") or []
    if not model:                return {"ok": None, "value": "no model configured"}
    if model in names:           return {"ok": True,  "value": f"{model} found on server"}
    near = suggest(model, names)
    tail = f" — did you mean {near}?" if near else ""
    return {"ok": None, "value": f"{model} not offered by the server ({len(names)} models listed){tail}"}
```

## DATA

```
  Model available       [WARN] Qwen-2.5-72b not offered by the server (14 models listed) — did you mean Qwen-2.5-72B?
  Model available       [WARN] could not verify (server does not expose /models)
  Model available       [OK]   Qwen-2.5-72B found on server
```

## TDD

1. Model present in the listing → `ok=True`.
2. Model absent, a near miss exists → `ok=None`, message contains
   `did you mean`.
3. Model absent, no near miss → `ok=None`, no `did you mean`.
4. `listing["ok"] is False` (auth/404) → `ok=None`, "does not expose /models",
   and no exception.
5. `model_check` never sets `overall_ok` to False.
6. Without `--check-models`, the key is absent entirely.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_11.md`.
> Implement step 11: add `_check_model_listed()` to
> `llm/providers/langchain/verification.py`, populate `result["model_check"]`
> under `--check-models`, reuse `utils.config_hints.suggest()` for near-misses,
> degrade to an exit-neutral "could not verify" when the server exposes no
> `/models`, and add the `"model_check"` label to `_LABEL_MAP`. The check is
> advisory and must never set `overall_ok` to False. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
