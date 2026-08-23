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
_REDIRECT_ENV: dict[str, tuple[str, ...]] = {
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

def redirect_env_in_effect(backend: str | None) -> str | None:
    """Return the first set redirect env var for *backend*, or None."""
```

## HOW

- `dialed_url` reads `chat_model.root_client.base_url` (both `ChatOpenAI` and
  `AzureChatOpenAI` expose it) and falls back to `chat_model.base_url`
  (`ChatOllama`). Returns `None` when neither exists.
- `resolve_target` constructs via `_create_chat_model(config, timeout=5)` —
  local, no network — inside `try/except Exception`. On failure it returns the
  config value (or `"(not configured)"`) with `verified=False` and a source that
  says so. Construction can fail for two legitimate reasons: the backend package
  is not installed, or the step-5 contract is violated.
- **Close both httpx clients** after inspection: `create_openai_model` builds a
  sync and an async client per call and nothing closes them. Use a `finally`
  block; `http_client.close()` and `asyncio.run(http_async_client.aclose())`,
  each guarded by `getattr(..., None)` and try/except (`ChatOllama` has neither).
- `gemini` / `anthropic` return `ResolvedTarget("n/a", "backend has no
  configurable target", True)` without constructing anything.
- For `ollama` the resolution happens in *our* code (`_resolve_ollama_host` does
  `os.getenv("OLLAMA_HOST") or base_url`), so the source is knowable directly.

## ALGORITHM

```
resolve_target(config):
    backend = config["backend"]
    if backend not in ("openai", "ollama"): return ResolvedTarget("n/a", "...", True)
    try: model = _create_chat_model(config, timeout=5)
    except Exception: return ResolvedTarget(config.get("base_url") or "(not configured)",
                                            "config.toml (unverified — client not constructed)", False)
    try: url = dialed_url(model) or "(unknown)"
    finally: _close_http_clients(model)
    return ResolvedTarget(url, _source_for(config, backend, url), True)

_source_for(config, backend, url):
    cfg = config.get("base_url")
    if cfg and url.rstrip("/").startswith(cfg.rstrip("/")): return "config.toml [llm.langchain] base_url"
    env = redirect_env_in_effect(backend)
    return f"{env} env var" if env else "SDK default"
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
3. Nothing set → url is the SDK default, source `"SDK default"`.
4. `_create_chat_model` raises → `verified is False`, url is the config value,
   source contains `unverified`.
5. `gemini` → `("n/a", ..., True)` and `_create_chat_model` is **not** called.
6. Both stub http clients are closed exactly once.
7. `ollama` reads `base_url` off the model, and `OLLAMA_HOST` is reported as the
   source when set.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`.
> Implement step 6: add `ResolvedTarget`, `dialed_url()`, `resolve_target()`,
> `redirect_env_in_effect()` and the `_REDIRECT_ENV` table to
> `llm/providers/langchain/_config_diagnostics.py`. Read the URL from the
> constructed client (never computed from config), close both httpx clients
> afterwards, return `n/a` for gemini/anthropic, and fall back to the
> config-derived value labelled *unverified* when construction fails.
> Write tests first (TDD) using a stub chat model, so no langchain install is
> required. Use MCP tools only. Run pytest (fast markers), pylint and mypy.
