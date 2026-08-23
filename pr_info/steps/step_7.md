# Step 7 — Effective-config echo + env-redirection flag

The highest-value verify addition: a block showing exactly what will be used,
including fallbacks and the *source* of each value.

## WHERE

- `src/mcp_coder/llm/providers/langchain/_config_diagnostics.py` — builder
- `src/mcp_coder/cli/commands/verify.py` — printing
- `tests/llm/providers/langchain/test_langchain_resolve_target.py` — builder tests
- `tests/cli/commands/test_verify_sections_orchestration.py` — rendering test

## WHAT

```python
def describe_effective_config(
    config: Mapping[str, str | None],
    api_key_source: str | None = None,
) -> list[tuple[str, str]]:
    """Return (label, value) rows describing the config that will actually be used."""
```

## HOW

- Returns plain tuples, **not** a result-dict sub-block. `_format_section` reads
  `ok`/`value` from every dict-valued entry and would render an echo block as an
  empty warning row; keeping the echo out of the dict removes that hazard rather
  than working around it, and keeps the echo out of exit-code logic by
  construction.
- `verify.py` prints it under its own header with an **empty marker**, which
  already renders without a status symbol:
  ```python
  print(_pad("EFFECTIVE CONFIG"))
  for label, value in describe_effective_config(config, key_source):
      print(_format_row(label, "", value, indent=2))
  ```
- `api_key` provenance comes from the existing
  `verification._resolve_api_key(backend, config_api_key)` → `(key, source)`;
  mask with the existing `_mask_api_key`. No new source resolver.
- **Redirection flag** (Decision 18): after the echo, when
  `redirect_env_in_effect(backend)` is set *and* the resolved URL differs from
  what config implies (config `base_url` unset, or the URL does not start with
  it), print one `[WARN]` row naming the variable. Printed only → exit-neutral.
- Place the section immediately before `LLM PROVIDER DETAILS`, inside the
  `active_provider == "langchain"` branch.

## ALGORITHM

```
describe_effective_config(config, api_key_source):
    target = resolve_target(config)
    mode   = "Azure OpenAI (api_version set)" if azure else "plain <backend> (api_version not set)"
    rows = [("backend", backend or "(not configured)"),
            ("mode", mode),
            ("model", model or "(not configured)"),
            ("base_url", f"{target.url}   ({target.source})"),
            ("api_key", f"{masked}   (from {api_key_source})" if masked else "(not set)")]
    return rows
```

## DATA

```
=== EFFECTIVE CONFIG ======================================================
  backend                       openai
  mode                          plain OpenAI (api_version not set)
  model                         Qwen-2.5-72B
  base_url                      https://api.openai.com/v1/   (SDK default)
  api_key                       Qwen...abcd   (from OPENAI_API_KEY env var)

  base_url redirected    [WARN] OPENAI_BASE_URL overrides config.toml — requests go to https://other.host/v1
```

Backends with no meaningful target show `base_url  n/a (backend has no
configurable target)`.

## TDD

1. Builder returns five rows in a stable order; `mode` names `api_version` as
   the discriminator in both directions.
2. `base_url` row carries the target's source verbatim; unverified targets keep
   the `unverified` wording.
3. `gemini` → `n/a`.
4. Rendering test: the echo appears with **no** `[OK]`/`[WARN]` symbols and the
   exit code is unchanged.
5. Redirect flag: `OPENAI_BASE_URL` set and config `base_url` unset → warning row
   printed; no redirect env set → no row.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`.
> Implement step 7: add `describe_effective_config()` to
> `_config_diagnostics.py` returning `list[tuple[str, str]]`, and print it from
> `cli/commands/verify.py` as an EFFECTIVE CONFIG section using
> `_format_row(label, "", value, indent=2)` (no status symbols, not part of the
> result dict, not part of the exit code). Reuse `_resolve_api_key` and
> `_mask_api_key` for the api_key row. Add the exit-neutral redirect-env-var
> warning driven by `redirect_env_in_effect()`. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
