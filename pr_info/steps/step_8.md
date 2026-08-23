# Step 8 — Rebase the base-URL shape check on the resolved target

`_check_base_url_shape` (renamed in step 1, `verification.py:129-170`) currently
validates the raw config string. Two concrete inaccuracies: it returns `None`
when the config value is unset — staying silent exactly when `OPENAI_BASE_URL`
is redirecting — and when config *is* set but an env var overrides it, it
validates a string the client never uses.

## WHERE

- `src/mcp_coder/llm/providers/langchain/verification.py`
- `tests/llm/providers/langchain/test_langchain_verification.py`

## WHAT

```python
def _check_base_url_shape(
    target: ResolvedTarget, api_version: str | None
) -> dict[str, Any] | None:
    """Pure string heuristic against the URL the client will actually dial."""
```

## HOW

- The three heuristics are **unchanged** — `/completions` substring, malformed
  URL (scheme/netloc), missing `/v1` suffix. Only the input changes.
- **Keep the Azure skip.** Azure's resolved client URL is
  `https://res.openai.azure.com/openai/deployments/<deployment>/`, so the `/v1`
  heuristic would fire on a *correct* Azure config. Rebasing removes the
  config-string reason the skip was safe, so it must stay explicit:
  `if api_version: return None`.
- Also skip when `target.url` is `"n/a"`.
- Append the provenance to every returned `value`:
  `f"{message} (source: {target.source})"`.
- Stays advisory: `ok` is only `True` or `None`, never `False`, and
  `base_url_shape` never contributes to `overall_ok`.
- Call site in `verify_langchain` passes the `ResolvedTarget` from step 6 (one
  `resolve_target()` call per verify run — share it with step 7 rather than
  constructing the model twice).

## ALGORITHM

```
_check_base_url_shape(target, api_version):
    if api_version or target.url == "n/a": return None
    url = target.url
    if "/completions" in url: return warn(f"{url} — contains '/completions' ... (source: ...)")
    if urlparse(url) lacks http(s) scheme or netloc: return warn(f"{url} — malformed ...")
    if not url.rstrip("/").endswith("/v1"): return ok(f"{url} — most relays use .../v1")
    return ok(f"{url} (source: {target.source})")
```

## DATA

Unchanged entry shape, rendered under the `"Base URL"` label:

```
  Base URL              [WARN] https://api.openai.com/v1/ — most relays use .../v1 (source: SDK default)
```

## TDD

1. Config unset, `OPENAI_BASE_URL` redirecting to a malformed URL → the check now
   **fires** (previously silent).
2. Config set but overridden by env → the heuristic runs on the env value, and
   the message names the env var as the source.
3. `api_version` set → returns `None` (Azure skip preserved), even though the
   resolved Azure URL would otherwise trip the `/v1` rule.
4. `n/a` target (gemini) → `None`.
5. The existing `/completions` and malformed-URL cases keep their wording.
6. `base_url_shape` never sets `ok=False` and never changes `overall_ok`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_8.md`.
> Implement step 8: change `_check_base_url_shape` in
> `llm/providers/langchain/verification.py` to take the `ResolvedTarget` from
> step 6 instead of the raw config string, keeping the three existing heuristics
> verbatim, keeping the Azure skip explicit, skipping `n/a` targets, and
> appending the source to the reported value. It stays advisory and must never
> affect `overall_ok`. Reuse the single `resolve_target()` call already made for
> the effective-config echo. Write tests first (TDD), including the
> previously-silent `OPENAI_BASE_URL` redirect case.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
