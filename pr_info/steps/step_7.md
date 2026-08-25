# Step 7 — Effective-config echo + env-redirection flag + api_key override flag

The highest-value verify addition: a block showing exactly what will be used,
including fallbacks and the *source* of each value.

## WHERE

- `src/mcp_coder/llm/providers/langchain/_config_diagnostics.py` — builder
- `src/mcp_coder/llm/providers/langchain/verification.py` — the **single**
  `resolve_target()` call, `_resolve_api_key` re-key + extension, and the two
  new rows
- `src/mcp_coder/cli/commands/verify_formatting.py` — two `_LABEL_MAP` entries
- `src/mcp_coder/cli/commands/verify.py` — printing only
- `tests/llm/providers/langchain/test_langchain_resolve_target.py` — builder tests
- `tests/llm/providers/langchain/test_langchain_verification.py` — wiring tests
- `tests/cli/commands/test_verify_sections_orchestration.py` — rendering test

## WHAT

```python
# _config_diagnostics.py — pure formatting, does NOT resolve or mask anything
def describe_effective_config(
    config: Mapping[str, str | None],
    target: ResolvedTarget,
    *,
    api_key_masked: str | None = None,
    api_key_source: str | None = None,
    api_key_overridden: bool = False,
) -> list[tuple[str, str]]:
    """Return (label, value) rows describing the config that will actually be used.

    The three api_key arguments travel together and all come from the same
    `_resolve_api_key` call, so the printed value can never belong to a
    different source than the printed label.
    """

# verification.py — re-keyed by mode, third element added;
# verify_langchain is the only in-repo caller
def _resolve_api_key(
    mode: str | None, config_key: str | None
) -> tuple[str | None, str | None, bool]:
    """Return (key, source, overridden), resolving in the order the *client*
    resolves: primary env var > config.toml > the row's remaining env vars >
    `_KEYLESS_ENV`.

    *overridden* is True only in the primary-beats-config case. *source* may be
    set with *key* None — gemini's keyless Vertex carve-out satisfies the
    credential without exposing a readable value.
    """
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
api_key, key_source, key_overridden = _resolve_api_key(mode_of(config),
                                                       config_api_key)
result["effective_config"] = describe_effective_config(
    config, target,
    api_key_masked=_mask_api_key(api_key),
    api_key_source=key_source,
    api_key_overridden=key_overridden,
)
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
- **The `mode` row is guarded like the `backend` row.** When `mode_of(config)`
  returns `None` — `backend` unset or typo'd — there is no mode to name, so the
  row reads `(not applicable — backend not configured)`, never
  `plain None (api_version not set)`. Same reasoning as step 6's
  `_NO_BACKEND_TARGET`: this block must not assert a mode for a backend that does
  not exist, and it is the row next to `backend  (not configured)` and
  `base_url  (backend not configured)`.
- **The non-Azure parenthetical states the actual `api_version`.** `azure` is
  `mode_of(config) == "azure"`, true only for `openai` + `api_version`, so a
  `gemini`/`anthropic`/`ollama` config *with* a stray `api_version` takes the
  non-Azure branch. Hardcoding `(api_version not set)` there would print a false
  claim directly above step 9's
  `API version [WARN] api_version is ignored by backend 'gemini' — remove it` —
  precisely the misconfiguration this issue exists to surface. When the key is
  present the row reads `plain gemini (api_version ignored by gemini)` instead.
- **`_resolve_api_key` is re-keyed by *mode*, not backend.** It reads
  `_BACKEND_ENV_VARS` (`verification.py:24-29`) — one variable per *backend* —
  while step 5's contract accepts a *tuple* per *mode*, including
  `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_AD_TOKEN` and `GOOGLE_API_KEY`. Left as
  is, an Azure setup keyed off `AZURE_OPENAI_API_KEY` yields no contract finding
  *and* no resolved key, so this echo prints `api_key   (not set)` and step 9's
  no-finding default prints `API key [OK] not set (optional)` — a false
  provenance claim inside the one block whose entire purpose is truthful
  provenance, and "optional" is wrong because `api_key` is `required` in those
  rows. So: **delete `_BACKEND_ENV_VARS`**, import `_API_KEY_ENV`,
  `_KEYLESS_ENV` and `mode_of` from `_config_diagnostics` (same package,
  mirroring step 8's `_UNSET_TARGET` import), pass `mode_of(config)` instead of
  `backend` — the row then names the
  variable that actually supplied the key. Gemini's keyless Vertex carve-out has
  no readable key, so it returns
  `(None, "GOOGLE_GENAI_USE_VERTEXAI env var", False)`; the echo renders
  `(not set — satisfied via GOOGLE_GENAI_USE_VERTEXAI env var)` and step 9
  renders `satisfied via …` rather than `not set (optional)`. Step 9's `scoped`
  default keeps `not set (optional)` only for a genuinely optional-and-unset
  `api_key` (ollama).
- **The scan order is `_API_KEY_ENV[mode][0]` > config `api_key` > the rest of
  the row > `_KEYLESS_ENV`** — a straight scan of the whole row before config
  would report a source the client never reads. Only the **first** entry of each
  row is read by *our* code, and it genuinely beats config:
  `create_openai_model` does `os.getenv("OPENAI_API_KEY") or api_key`
  (`openai_backend.py:36`), and `create_gemini_model` / `create_anthropic_model`
  / `create_ollama_model` have the same shape for `GEMINI_API_KEY` /
  `ANTHROPIC_API_KEY` / `OLLAMA_API_KEY`. The remaining entries —
  `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_AD_TOKEN`, `GOOGLE_API_KEY` — are **SDK
  fallbacks that apply only when no key is passed at all**, so a config
  `api_key` beats them. Scanning the whole row first would, for an Azure config
  with both a config `api_key` and `AZURE_OPENAI_API_KEY` exported, print the
  wrong masked value under
  `(from AZURE_OPENAI_API_KEY env var — overrides config.toml api_key)` and add
  a false `API key override [WARN]` row, while the client quietly used the
  config key: fabricated provenance in the block whose whole purpose is truthful
  provenance. `overridden` is therefore set **only** in the primary-beats-config
  case.
  Step 5's `validate()` is unaffected: its `api_key` check tests *presence*
  across config, every env var in the row and the keyless carve-out, which is
  order-independent. The ordering matters for provenance only.
- **The api_key row's value, source and override flag are all passed in.**
  `describe_effective_config` never reads `config["api_key"]` for the value:
  the winning key frequently comes from the env var while config.toml holds a
  different (losing) one, so masking the config value under an
  `OPENAI_API_KEY env var` label would fabricate provenance — the exact bug
  class this issue exists to kill — and dropping the value would print
  `(not set)` for every env-var-sourced key. `verify_langchain` masks the
  resolved key with the existing `_mask_api_key` (which stays in
  `verification.py`, so `_config_diagnostics` gains no import back) and hands
  the masked string, its source and `overridden` to the builder. No new source
  resolver, no masking in `_config_diagnostics`.
- **Redirection flag** (Decision 18): keyed on the variable that *actually
  produced* the dialed URL, never on "some redirect variable is exported".
  `verify_langchain` asks `redirect_env_in_effect(config, target.url)` (step 6),
  which already applies both filters — mode-applicability
  (`AZURE_OPENAI_ENDPOINT` only in Azure mode) and a value match against
  `target.url` — and returns `None` for an exported-but-inert variable. The row
  is added only when that returns a variable **and** the target differs from
  what config implies (config `base_url` unset, or `target.url` does not match
  it):
  ```python
  cfg_base = config.get("base_url")
  env_var = redirect_env_in_effect(config, target.url)
  if env_var and not (cfg_base and _targets_match(cfg_base, target.url)):
      result["base_url_redirect"] = {"ok": None, "value":
          f"{env_var} overrides config.toml — requests go to {target.url}"}
  ```
  `_targets_match` is step 6's helper (declared in its module surface); reusing
  it keeps the "did config imply this URL?" comparison identical to the one
  `_source_for` makes, rather than adding a second, drift-prone predicate.
  Without the value match the row would fabricate exactly the kind of claim this
  issue exists to kill: a stale `AZURE_OPENAI_ENDPOINT` under a plain `openai`
  config, or `OPENAI_BASE_URL` when `OPENAI_API_BASE` is the one the client used,
  would print `X overrides config.toml — requests go to https://api.openai.com/v1/`
  when nothing was redirected at all.
  `_format_section` renders it as `[WARN]`; `overall_ok` is composed explicitly
  (step 9), so an `ok=None` row can never change the exit code.
- **api_key override flag** (acceptance criterion: "`verify` flags when
  `OPENAI_API_KEY` overrides a configured `api_key`"). Today `_resolve_api_key`
  returns only the *winning* source, so the fact that config.toml also had a key
  is invisible. It gains a third element `overridden: bool`, set when the env var
  won **and** `config_key` was non-empty. Two consequences:
  - the echo's `api_key` line reads
    `Qwen...abcd   (from OPENAI_API_KEY env var — overrides config.toml api_key)`;
  - `verify_langchain` adds an exit-neutral row, built from the **api-key**
    resolution and gated on `key_overridden` — never from `env_var`, which is
    bound a few lines above to `redirect_env_in_effect(...)`, a *base-URL*
    redirect variable that is `None` in most runs:
    ```python
    if key_overridden:                       # only the primary-beats-config case
        result["api_key_override"] = {"ok": None, "value":
            f"{key_source} overrides [llm.langchain] api_key in config.toml"}
    ```
    `key_source` already reads `"OPENAI_API_KEY env var"`, so no `env var`
    suffix is appended here.
  Only in-repo caller is `verify_langchain`; update it and the existing
  `_resolve_api_key` tests for the 3-tuple.
- `_LABEL_MAP` additions: `"base_url_redirect": "Base URL redirect"`,
  `"api_key_override": "API key override"`.

## ALGORITHM

```
describe_effective_config(config, target, *, api_key_masked, api_key_source,
                          api_key_overridden):
    if mode_of(config) is None:                    # backend unset or typo'd
        mode = "(not applicable — backend not configured)"
    else:
        azure = mode_of(config) == "azure"         # only openai + api_version
        note  = (f"api_version ignored by {backend}" if config.get("api_version")
                 else "api_version not set")
        mode  = "Azure OpenAI (api_version set)" if azure else f"plain <backend> ({note})"
    if api_key_masked is None:
        key_row = (f"(not set — satisfied via {api_key_source})"
                   if api_key_source else "(not set)")
    else:
        suffix  = " — overrides config.toml api_key" if api_key_overridden else ""
        key_row = f"{api_key_masked}   (from {api_key_source}{suffix})"
    rows = [("backend", backend or "(not configured)"),
            ("mode", mode),
            ("model", model or "(not configured)"),
            ("base_url", f"{target.url}   ({target.source})"),
            ("api_key", key_row)]
    return rows

_resolve_api_key(mode, config_key):                  # mode, not backend
    env_vars = _API_KEY_ENV.get(mode or "", ())      # step 5's mode-keyed tuple
    primary  = env_vars[0] if env_vars else None     # the only var our code reads
    if primary and os.environ.get(primary):          # create_*_model: getenv(X) or api_key
        return os.environ[primary], f"{primary} env var", bool(config_key)
    if config_key: return config_key, "config.toml", False
    for var in env_vars[1:]:                         # SDK fallbacks — reached only
        env_value = os.environ.get(var)              # when no key is passed at all
        if env_value: return env_value, f"{var} env var", False
    keyless = _KEYLESS_ENV.get(mode or "")           # gemini/Vertex: no readable key
    if keyless and os.environ.get(keyless):
        return None, f"{keyless} env var", False
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
   the discriminator in both directions. With `backend` unset, and again with
   `backend = "opnai"` (`mode_of` → `None`), the `mode` row reads
   `(not applicable — backend not configured)` and never contains `None` —
   matching the `backend` row's `(not configured)` and step 6's
   `_NO_BACKEND_TARGET` wording for the same config. And with
   `backend = "gemini"` **plus** `api_version` set (step 5's TDD 5
   misconfiguration): the row takes the non-Azure branch but must not claim
   `api_version not set` — it names the ignored key, agreeing with step 9's
   `API version [WARN] ... ignored by backend 'gemini'` row below it.
2. `base_url` row carries the passed target's source verbatim; unverified
   targets keep the `unverified` wording. The builder never calls
   `resolve_target` itself (assert with a patched module attribute).
3. `gemini` → `n/a`.
3b. api_key row provenance: with `api_key_masked="Qwen...abcd"`,
   `api_key_source="OPENAI_API_KEY env var"` and `api_key_overridden=True`, the
   row shows **that** masked value, names the env var and appends the override
   text — assert the config dict's own (losing) `api_key` value never appears.
   `api_key_masked=None` **and** `api_key_source=None` is the only input pair
   that yields a bare `(not set)`.
3c. Mode-keyed resolution (guards the false `(not set)` / `[OK] not set
   (optional)` pair). All credential vars cleared, then parametrised: Azure mode
   with only `AZURE_OPENAI_API_KEY`, again with only `AZURE_OPENAI_AD_TOKEN`,
   and `gemini` with only `GOOGLE_API_KEY` → `_resolve_api_key` returns that key
   with the matching `"<VAR> env var"` source and the echo row names it.
   `gemini` with only `GOOGLE_GENAI_USE_VERTEXAI` → key is `None`, source names
   that variable, row reads
   `(not set — satisfied via GOOGLE_GENAI_USE_VERTEXAI env var)`. Nothing set →
   `(None, None, False)` and a bare `(not set)`.
3d. Config key beats a *secondary* env var: Azure mode with a config `api_key`,
   `OPENAI_API_KEY` cleared and `AZURE_OPENAI_API_KEY` exported → source is
   `"config.toml"`, `overridden is False`, and `verify_langchain` adds **no**
   `api_key_override` row. Same shape for `gemini` with a config `api_key` and
   only `GOOGLE_API_KEY` exported. The primary var still wins: config `api_key`
   plus `OPENAI_API_KEY` → source names `OPENAI_API_KEY` and
   `overridden is True` (case 7).
4. Wiring: `verify_langchain` calls `resolve_target` **exactly once** per run
   (patch and count) and puts a list under `result["effective_config"]`.
5. Rendering test: the echo appears with **no** `[OK]`/`[WARN]` symbols, is not
   rendered inside LLM PROVIDER DETAILS, and the exit code is unchanged.
6. Redirect flag: `OPENAI_BASE_URL` set, config `base_url` unset and the target
   reporting the env value → the `base_url_redirect` row is present with
   `ok=None`; no redirect env set → the key is absent.
6b. Redirect flag does **not** fire on an inert variable: plain `openai` (no
   `api_version`), config `base_url` unset, a stale `AZURE_OPENAI_ENDPOINT`
   exported, target resolving to the SDK default → the `base_url_redirect` key
   is **absent** and the echo's `base_url` row reads `(SDK default)`. Same for
   `OPENAI_BASE_URL` when `OPENAI_API_BASE` is the value the target matches:
   only the matching variable is named, and only once.
7. api_key override: env var **and** config `api_key` set → `overridden is True`,
   `api_key_override` row present, echo line names the override, `overall_ok`
   unchanged. Assert the row's **rendered text**, not just its presence: it
   names the api-key variable (`OPENAI_API_KEY env var overrides …`). Run the
   same config twice — once with a base-URL redirect variable also exported
   (`OPENAI_BASE_URL`), once with none — and assert the text is identical and
   contains neither a redirect variable name nor `None`, pinning that the row is
   built from `key_source` and not from `redirect_env_in_effect`. Env var set
   with **no** config key → no row, no "overrides" text.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`.
> Implement step 7: add
> `describe_effective_config(config, target, *, api_key_masked, api_key_source,
> api_key_overridden)` to `_config_diagnostics.py` returning
> `list[tuple[str, str]]` (pure formatting — it must **not** call
> `resolve_target`, mask anything, or read `config["api_key"]` for the api_key
> row: the masked value, its source and the override flag all arrive from the
> same `_resolve_api_key` call in `verify_langchain`, so the row can never show
> one source's value under another source's label). In `verify_langchain`, make the single
> `resolve_target(config)` call of the run, store the rows as the list-valued
> `result["effective_config"]`, and add the exit-neutral `base_url_redirect` and
> `api_key_override` rows. Build the `api_key_override` row's text from
> `key_source` and gate it on `key_overridden` — **not** from the `env_var`
> local, which holds the base-URL redirect variable and is usually `None`. Guard
> the echo's `mode` row on `mode_of(config) is None` (`backend` unset or typo'd)
> and render `(not applicable — backend not configured)` rather than
> `plain None (api_version not set)`. In the non-Azure branch derive the
> parenthetical from the config (`azure = mode_of(config) == "azure"`): say
> `api_version not set` only when it really is unset, otherwise
> `api_version ignored by <backend>` — a `gemini` config with a stray
> `api_version` must not contradict step 9's `[WARN] ... ignored` row.
> Key the redirect row on
> `redirect_env_in_effect(config, target.url)` — the variable whose value
> actually produced the dialed URL — so an exported-but-inert variable (a stale
> `AZURE_OPENAI_ENDPOINT` under plain `openai`, or `OPENAI_BASE_URL` when
> `OPENAI_API_BASE` won) produces **no** row. Guard it with step 6's
> `_targets_match(config["base_url"], target.url)` — do not invent a second
> predicate. Re-key `_resolve_api_key` on the **mode**: delete
> `_BACKEND_ENV_VARS` and resolve in the order the client resolves —
> `_API_KEY_ENV[mode][0]` (the only variable our own `create_*_model` reads, and
> it beats config) > config `api_key` > the row's remaining variables (SDK
> fallbacks that apply only when no key is passed at all) > `_KEYLESS_ENV[mode]`
> — so an Azure key in `AZURE_OPENAI_API_KEY` (or a gemini key in
> `GOOGLE_API_KEY`) is named as the source instead of rendering `(not set)`,
> while a *configured* key with only a secondary variable exported still reports
> `config.toml`. Do **not** scan the whole row before config: that would name a
> source the client never read. Extend it to return `(key, source, overridden)`,
> setting `overridden` only in the primary-beats-config case, so an
> `OPENAI_API_KEY` that beats a configured `api_key` is flagged rather than
> silently winning — and a secondary variable that lost never is. Add the two `_LABEL_MAP`
> entries. `cli/commands/verify.py` only *prints* the EFFECTIVE CONFIG section via
> `_format_row(label, "", value, indent=2)` — it must not load config or call
> private llm helpers itself. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
