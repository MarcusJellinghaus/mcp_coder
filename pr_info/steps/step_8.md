# Step 8 — Rebase the base-URL shape check on the resolved target

`_check_base_url_shape` (renamed in step 1, `verification.py:129-170`) currently
validates the raw config string. Two concrete inaccuracies: it returns `None`
when the config value is unset — staying silent exactly when `OPENAI_BASE_URL`
is redirecting — and when config *is* set but an env var overrides it, it
validates a string the client never uses.

This step also carries the deferred half of Decision 19: the result key
`endpoint_shape` → `base_url_shape` and its `_LABEL_MAP` label
`"Endpoint"` → `"Base URL"`, split out of step 1 (which is large enough
without it, and which the issue outline itself calls separable).

## WHERE

- `src/mcp_coder/llm/providers/langchain/verification.py`
- `src/mcp_coder/cli/commands/verify_formatting.py` — `_LABEL_MAP:113`
- `tests/llm/providers/langchain/test_langchain_verification.py`
- `tests/cli/commands/test_verify_format_pad.py`

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
- **Call-site gate: unchanged — stays `if backend == "openai"`**
  (`verification.py:260`). The `/v1` convention is an OpenAI/relay convention;
  a valid ollama host is `http://localhost:11434` with no `/v1`, so broadening
  the gate would warn on correct ollama configs. The `OLLAMA_HOST` redirect is
  therefore **not** covered here — it is surfaced by step 7's
  `base_url_redirect` row and the effective-config echo, which is what the
  acceptance criterion asks for (the shape criterion names only the
  `OPENAI_BASE_URL` case). Result key becomes
  `result["base_url_shape"]`.
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
- **Plumbing (concrete).** Step 7 makes `verify_langchain` the owner of the
  single `resolve_target(config)` call of the run and binds it to a local
  `target`. This step passes that **same local** into the check:
  ```python
  if backend == "openai":
      shape = _check_base_url_shape(target, config.get("api_version"))
      if shape is not None:
          result["base_url_shape"] = shape
  ```
  No second resolution, no second chat-model construction, no new parameter on
  `verify_langchain`. (Ordering: step 7 before step 8. If step 8 is implemented
  first, it must introduce the `target = resolve_target(config)` local itself and
  step 7 then reuses it — either way there is exactly one call.)

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
7. `ollama` with `OLLAMA_HOST=http://localhost:11434` → **no** shape row at all
   (gate unchanged), while step 7's `base_url_redirect` row still reports it.
8. `resolve_target` is called exactly once per `verify_langchain` run with both
   the echo and the shape check active.
9. The result key is `base_url_shape` and renders under the `"Base URL"` label;
   no `verify` output says "Endpoint".

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_8.md`.
> Implement step 8: change `_check_base_url_shape` in
> `llm/providers/langchain/verification.py` to take the `ResolvedTarget` from
> step 6 instead of the raw config string, keeping the three existing heuristics
> verbatim, keeping the Azure skip explicit, skipping `n/a` targets, and
> appending the source to the reported value. It stays advisory and must never
> affect `overall_ok`. Pass the `target` local that `verify_langchain` already
> binds from its single `resolve_target(config)` call (step 7) — the chat model
> must not be constructed twice per run. Keep the call-site gate at
> `backend == "openai"`. In the same commit, rename the result key
> `endpoint_shape` → `base_url_shape` and the `_LABEL_MAP` label `"Endpoint"` →
> `"Base URL"` (Decision 19, split out of step 1). Write tests first (TDD),
> including the previously-silent `OPENAI_BASE_URL` redirect case.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
