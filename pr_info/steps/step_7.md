# Step 7 — Effective-config echo + env-redirection flag + api_key override flag

The highest-value verify addition: a block showing exactly what will be used,
including fallbacks and the *source* of each value.

## WHERE

- `src/mcp_coder/llm/providers/langchain/_config_diagnostics.py` — builder
- `src/mcp_coder/llm/providers/langchain/verification.py` — the **single**
  `resolve_target()` call, `_resolve_api_key` extension, and the two new rows
- `src/mcp_coder/cli/commands/verify_formatting.py` — two `_LABEL_MAP` entries
- `src/mcp_coder/cli/commands/verify.py` — printing only
- `tests/llm/providers/langchain/test_langchain_resolve_target.py` — builder tests
- `tests/llm/providers/langchain/test_langchain_verification.py` — wiring tests
- `tests/cli/commands/test_verify_sections_orchestration.py` — rendering test

## WHAT

```python
# _config_diagnostics.py — pure formatting, does NOT resolve anything itself
def describe_effective_config(
    config: Mapping[str, str | None],
    target: ResolvedTarget,
    api_key_source: str | None = None,
) -> list[tuple[str, str]]:
    """Return (label, value) rows describing the config that will actually be used."""

# verification.py — third element added; verify_langchain is the only in-repo caller
def _resolve_api_key(
    backend: str | None, config_key: str | None
) -> tuple[str | None, str | None, bool]:
    """Return (key, source, overridden) — *overridden* is True when the backend
    env var won while config.toml also had an api_key."""
```

## HOW

**Ownership of the resolution — one call per `verify` run.** `verify_langchain`
already loads `config` (`verification.py:191`) and resolves the api key
(`:211`). It therefore also makes the **single** `resolve_target(config)` call
and hands the resulting `ResolvedTarget` to both consumers: the echo builder
here and `_check_base_url_shape` in step 8. Nothing constructs a chat model
twice, and `verify.py` needs no access to the private llm-layer helpers
(`_load_langchain_config`, `_resolve_api_key`) and makes no second config load.

```python
# verify_langchain
target = resolve_target(config)                      # the one and only call
api_key, key_source, key_overridden = _resolve_api_key(backend, config_api_key)
result["effective_config"] = describe_effective_config(config, target, key_source)
```

- `result["effective_config"]` is a **list**, not a dict, so `_format_section`
  skips it outright (`verify_formatting.py:190-191`: non-dict entries are
  `continue`d), `_collect_install_hints` skips it (same isinstance guard) and
  `_compute_exit_code` never sees it. The "rendered without status symbols and
  excluded from exit-code logic" requirement is structural, not a workaround.
- `verify.py` prints it under its own header with an **empty marker**, which
  already renders without a status symbol:
  ```python
  print(_pad("EFFECTIVE CONFIG"))
  for label, value in langchain_result["effective_config"]:
      print(_format_row(label, "", value, indent=2))
  ```
  Placed immediately before `_format_section("LLM PROVIDER DETAILS", ...)`,
  inside the existing `active_provider == "langchain"` branch (`verify.py:421`).
- `api_key` provenance comes from `_resolve_api_key`; mask with the existing
  `_mask_api_key`. No new source resolver.
- **Redirection flag** (Decision 18): when `redirect_env_in_effect(backend)` is
  set *and* the resolved URL differs from what config implies (config `base_url`
  unset, or the URL does not start with it), `verify_langchain` adds
  ```python
  result["base_url_redirect"] = {"ok": None, "value":
      f"{env_var} overrides config.toml — requests go to {target.url}"}
  ```
  `_format_section` renders it as `[WARN]`; `overall_ok` is composed explicitly
  (step 9), so an `ok=None` row can never change the exit code.
- **api_key override flag** (acceptance criterion: "`verify` flags when
  `OPENAI_API_KEY` overrides a configured `api_key`"). Today `_resolve_api_key`
  returns only the *winning* source, so the fact that config.toml also had a key
  is invisible. It gains a third element `overridden: bool`, set when the env var
  won **and** `config_key` was non-empty. Two consequences:
  - the echo's `api_key` line reads
    `Qwen...abcd   (from OPENAI_API_KEY env var — overrides config.toml api_key)`;
  - `verify_langchain` adds an exit-neutral row
    ```python
    result["api_key_override"] = {"ok": None, "value":
        f"{env_var} env var overrides [llm.langchain] api_key in config.toml"}
    ```
  Only in-repo caller is `verify_langchain`; update it and the existing
  `_resolve_api_key` tests for the 3-tuple.
- `_LABEL_MAP` additions: `"base_url_redirect": "Base URL redirect"`,
  `"api_key_override": "API key override"`.

## ALGORITHM

```
describe_effective_config(config, target, api_key_source):
    mode   = "Azure OpenAI (api_version set)" if azure else "plain <backend> (api_version not set)"
    rows = [("backend", backend or "(not configured)"),
            ("mode", mode),
            ("model", model or "(not configured)"),
            ("base_url", f"{target.url}   ({target.source})"),
            ("api_key", f"{masked}   (from {api_key_source})" if masked else "(not set)")]
    return rows

_resolve_api_key(backend, config_key):
    env_value = os.environ.get(_BACKEND_ENV_VARS.get(backend or "", ""))
    if env_value: return env_value, f"{env_var} env var", bool(config_key)
    if config_key: return config_key, "config.toml", False
    return None, None, False
```

## DATA

```
=== EFFECTIVE CONFIG ======================================================
  backend                       openai
  mode                          plain OpenAI (api_version not set)
  model                         Qwen-2.5-72B
  base_url                      https://api.openai.com/v1/   (SDK default)
  api_key                       Qwen...abcd   (from OPENAI_API_KEY env var — overrides config.toml api_key)

=== LLM PROVIDER DETAILS ==================================================
  ...
  Base URL redirect     [WARN] OPENAI_BASE_URL overrides config.toml — requests go to https://other.host/v1
  API key override      [WARN] OPENAI_API_KEY env var overrides [llm.langchain] api_key in config.toml
```

Backends with no meaningful target show `base_url  n/a (backend has no
configurable target)`.

## TDD

1. Builder returns five rows in a stable order; `mode` names `api_version` as
   the discriminator in both directions.
2. `base_url` row carries the passed target's source verbatim; unverified
   targets keep the `unverified` wording. The builder never calls
   `resolve_target` itself (assert with a patched module attribute).
3. `gemini` → `n/a`.
4. Wiring: `verify_langchain` calls `resolve_target` **exactly once** per run
   (patch and count) and puts a list under `result["effective_config"]`.
5. Rendering test: the echo appears with **no** `[OK]`/`[WARN]` symbols, is not
   rendered inside LLM PROVIDER DETAILS, and the exit code is unchanged.
6. Redirect flag: `OPENAI_BASE_URL` set and config `base_url` unset → the
   `base_url_redirect` row is present with `ok=None`; no redirect env set → the
   key is absent.
7. api_key override: env var **and** config `api_key` set → `overridden is True`,
   `api_key_override` row present, echo line names the override, `overall_ok`
   unchanged. Env var set with **no** config key → no row, no "overrides" text.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`.
> Implement step 7: add `describe_effective_config(config, target, api_key_source)`
> to `_config_diagnostics.py` returning `list[tuple[str, str]]` (pure formatting —
> it must **not** call `resolve_target`). In `verify_langchain`, make the single
> `resolve_target(config)` call of the run, store the rows as the list-valued
> `result["effective_config"]`, and add the exit-neutral `base_url_redirect` and
> `api_key_override` rows. Extend `_resolve_api_key` to return
> `(key, source, overridden)` so an `OPENAI_API_KEY` that beats a configured
> `api_key` is flagged rather than silently winning. Add the two `_LABEL_MAP`
> entries. `cli/commands/verify.py` only *prints* the EFFECTIVE CONFIG section via
> `_format_row(label, "", value, indent=2)` — it must not load config or call
> private llm helpers itself. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
