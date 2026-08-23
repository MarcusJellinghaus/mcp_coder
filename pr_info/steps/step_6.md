# Step 6 — `resolve_target()`: read the dialed URL off the constructed client

Measured SDK behaviour: `ChatOpenAI(base_url=None)` leaves the langchain field
`None` while the `openai` SDK dials `OPENAI_BASE_URL` when set, else
`https://api.openai.com/v1/`. Any target computed from config is therefore wrong
whenever that variable is exported. Shared by steps 7, 8 and 10.

## WHERE

- `src/mcp_coder/llm/providers/langchain/_config_diagnostics.py` (extends step 5)
- **New:** `tests/llm/providers/langchain/test_langchain_resolve_target.py`

## WHAT

```python
# Sentinel used when nothing resolves; step 8 skips the shape check on it.
_UNSET_TARGET = "(not configured)"

_REDIRECT_ENV: dict[str, tuple[str, ...]] = {   # keyed by backend, not by mode
    "openai": ("OPENAI_BASE_URL", "OPENAI_API_BASE", "AZURE_OPENAI_ENDPOINT"),
    "ollama": ("OLLAMA_HOST",),
}

@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    url: str          # dialed URL, "n/a", or the config fallback
    source: str       # human-readable provenance
    verified: bool    # True when read from a constructed client

def dialed_url(chat_model: Any) -> str | None:
    """Read the base URL off a constructed chat model, or None if it has none."""

def resolve_target(config: Mapping[str, str | None]) -> ResolvedTarget:
    """Construct the chat model locally and report the URL it would dial."""

def redirect_env_in_effect(
    config: Mapping[str, str | None], url: str
) -> str | None:
    """Return the redirect env var that actually produced *url*, or None.

    A variable is only named when it is applicable to the current
    backend/mode **and** its value matches the URL the client will dial.
    """
```

## HOW

- `dialed_url` reads `chat_model.root_client.base_url` (both `ChatOpenAI` and
  `AzureChatOpenAI` expose it) and falls back to `chat_model.base_url`
  (`ChatOllama`). Returns `None` when neither exists.
- **Deferred import — mandatory.** Step 5 has `__init__.py` import `validate`
  from `_config_diagnostics` at module level, so `_config_diagnostics` must
  **not** import the package `__init__` at module level: that cycle makes
  `import mcp_coder.llm.providers.langchain` fail with a
  partially-initialised-module `ImportError`. Put the import **inside**
  `resolve_target`, mirroring how `verification.py` does `from . import _models`
  inside its functions:
  ```python
  def resolve_target(config):
      from . import _create_chat_model  # deferred: avoids the package cycle
  ```
  Cover it with a test that imports the package top-level (`import
  mcp_coder.llm.providers.langchain`) after step 5's wiring exists; the repo's
  `pycycle` check also guards this.
- `resolve_target` constructs via `_create_chat_model(config, timeout=5)` —
  local, no network — inside `try/except Exception`. On failure it returns the
  config value (or the `_UNSET_TARGET` sentinel) with `verified=False` and a
  source that says so. Export `_UNSET_TARGET` as a module constant: step 8 skips
  its shape heuristics on it, and a duplicated string literal there would drift.
  Construction can fail for two legitimate reasons: the backend package is not
  installed, or the step-5 contract is violated.
- **Close both httpx clients** after inspection: `create_openai_model` builds a
  sync and an async client per call and nothing closes them. Use a `finally`
  block; `http_client.close()` and `asyncio.run(http_async_client.aclose())`,
  each guarded by `getattr(..., None)` and try/except (`ChatOllama` has neither).
- `gemini` / `anthropic` return `ResolvedTarget("n/a", "backend has no
  configurable target", True)` without constructing anything.
- For `ollama` the resolution happens in *our* code (`_resolve_ollama_host` does
  `os.getenv("OLLAMA_HOST") or base_url`), so the source is knowable directly.
- **Never fabricate provenance.** "A redirect variable is exported" is *not*
  evidence that it produced the URL. Two filters, both mandatory, before a
  variable may be named as the source:
  - **Applicability by mode.** `AZURE_OPENAI_ENDPOINT` only ever applies in
    Azure mode (`openai` + `api_version`); `OPENAI_BASE_URL` / `OPENAI_API_BASE`
    only apply outside it. A stale `AZURE_OPENAI_ENDPOINT` left over from an
    earlier Azure attempt is inert for a plain-`openai` config.
  - **Value match against the dialed URL.** Even an applicable variable is named
    only when its value matches `url` (`_targets_match`). This settles the
    `OPENAI_BASE_URL` + `OPENAI_API_BASE` both-set case without guessing the
    SDK's precedence: whichever one the client actually used is the one whose
    value matches.

  With no applicable, matching variable and no config `base_url`, the source is
  `"SDK default"` — which is the truth for a plain-`openai` config resolving to
  `https://api.openai.com/v1/`, whatever else is exported.
- `_targets_match` tolerates the two normalisations in play: a trailing slash
  (Azure appends `openai/deployments/<deployment>/` to the configured resource
  URL) and a missing scheme (`OLLAMA_HOST` may be a bare `host:port`, which
  `_resolve_ollama_host` normalises to `http://host:port`).

## ALGORITHM

```
resolve_target(config):
    backend = config["backend"]
    if backend not in ("openai", "ollama"): return ResolvedTarget("n/a", "...", True)
    try: model = _create_chat_model(config, timeout=5)
    except Exception: return ResolvedTarget(config.get("base_url") or _UNSET_TARGET,
                                            "config.toml (unverified — client not constructed)", False)
    try: url = dialed_url(model) or "(unknown)"
    finally: _close_http_clients(model)
    return ResolvedTarget(url, _source_for(config, url), True)

_source_for(config, url):
    cfg = config.get("base_url")
    if cfg and _targets_match(cfg, url): return "config.toml [llm.langchain] base_url"
    env = redirect_env_in_effect(config, url)
    return f"{env} env var" if env else "SDK default"

_applicable_redirect_envs(config):
    backend = config.get("backend")
    azure = backend == "openai" and bool(config.get("api_version"))
    for name in _REDIRECT_ENV.get(backend or "", ()):
        if (name == "AZURE_OPENAI_ENDPOINT") == azure:   # mode-applicable only
            yield name

redirect_env_in_effect(config, url):
    for name in _applicable_redirect_envs(config):
        value = os.environ.get(name)
        if value and _targets_match(value, url): return name
    return None                       # exported but inert → not the source

_targets_match(candidate, url):
    c, u = candidate.rstrip("/"), url.rstrip("/")
    if "://" not in c: u = u.split("://", 1)[-1]   # OLLAMA_HOST may be host:port
    return u.startswith(c)
```

## DATA

```python
ResolvedTarget(url="https://api.openai.com/v1/",
               source="SDK default", verified=True)
ResolvedTarget(url="https://relay.internal/v1",
               source="OPENAI_BASE_URL env var", verified=True)
ResolvedTarget(url="https://relay.internal/v1",
               source="config.toml (unverified — client not constructed)",
               verified=False)
```

## TDD

Mock `_create_chat_model` to return a stub exposing `root_client.base_url` plus
recording `close()` / `aclose()` calls — no langchain install needed.

1. config `base_url` set and echoed by the client → source names the config key.
2. config unset, `OPENAI_BASE_URL` set (monkeypatch) → url is the env value,
   source names `OPENAI_BASE_URL`.
2b. Both `OPENAI_BASE_URL` and `OPENAI_API_BASE` set to *different* values → the
   variable named is the one whose value matches the URL the stub client
   reports, not the first entry in `_REDIRECT_ENV`.
3. Nothing set → url is the SDK default, source `"SDK default"`.
3b. **Stale `AZURE_OPENAI_ENDPOINT` with plain `openai`** (no `api_version`, no
   config `base_url`, client reports the SDK default) → source is
   `"SDK default"` and `redirect_env_in_effect(config, url)` returns `None`.
   The inert variable must never be named as the source.
3c. Azure mode (`openai` + `api_version`, no config `base_url`,
   `AZURE_OPENAI_ENDPOINT` set, client reports
   `https://res.openai.azure.com/openai/deployments/dep/`) → source names
   `AZURE_OPENAI_ENDPOINT` (prefix match, trailing-slash tolerant).
4. `_create_chat_model` raises → `verified is False`, url is the config value,
   source contains `unverified`.
5. `gemini` → `("n/a", ..., True)` and `_create_chat_model` is **not** called.
6. Both stub http clients are closed exactly once.
7. `ollama` reads `base_url` off the model, and `OLLAMA_HOST` is reported as the
   source when set.
8. `import mcp_coder.llm.providers.langchain` succeeds (cycle regression guard
   for the deferred import).

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`.
> Implement step 6: add `ResolvedTarget`, `dialed_url()`, `resolve_target()`,
> `redirect_env_in_effect()` and the `_REDIRECT_ENV` table to
> `llm/providers/langchain/_config_diagnostics.py`. Read the URL from the
> constructed client (never computed from config), close both httpx clients
> afterwards, return `n/a` for gemini/anthropic, and fall back to the
> config-derived value labelled *unverified* when construction fails.
> `redirect_env_in_effect(config, url)` takes the config **and** the resolved
> URL: name a redirect variable only when it is applicable to the current
> backend/mode (`AZURE_OPENAI_ENDPOINT` in Azure mode only) **and** its value
> matches the dialed URL. A merely-exported variable is inert and must not be
> reported as the source — a stale `AZURE_OPENAI_ENDPOINT` with a plain `openai`
> config resolving to `https://api.openai.com/v1/` reports `SDK default`. Import
> `_create_chat_model` **inside** `resolve_target` (function-level) — a
> module-level import from the package `__init__` would create an import cycle
> with step 5's wiring and break `import mcp_coder.llm.providers.langchain`.
> Write tests first (TDD) using a stub chat model, so no langchain install is
> required. Use MCP tools only. Run pytest (fast markers), pylint and mypy.
