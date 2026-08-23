# Step 4 — `_load_langchain_config()` must never raise

Prerequisite for every later step. The loader runs on **every** `verify`, even
when claude is the active provider (`verify.py:270`, the backend-readiness
warning). Today `get_config_values` raises `ValueError` on a schema type
mismatch (`user_config.py:299-308`), so `[llm.langchain] model = 123` makes a
claude user's `verify` print a clean config error and *then* traceback.

## WHERE

- `src/mcp_coder/llm/providers/langchain/__init__.py` — `_load_langchain_config`
- `tests/llm/providers/langchain/test_langchain_provider.py`
- `tests/cli/commands/test_verify_orchestration.py` (regression: verify survives
  a mistyped langchain value)

## WHAT

Signature unchanged:

```python
def _load_langchain_config() -> dict[str, str | None]:
    """Read [llm] and [llm.langchain] from config.toml. Never raises."""
```

## HOW

Wrap the `get_config_values` call. A type mismatch is already reported as an
error entry by `verify_config()` one section earlier, so the loader only needs to
degrade gracefully — not to re-report:

```python
try:
    raw = get_config_values([...])
except ValueError:
    logger.warning(
        "Ignoring [llm.langchain] config: schema type mismatch "
        "(see the CONFIG section of `mcp-coder verify`)."
    )
    raw = {}
```

Then read with `raw.get(key)` instead of `raw[key]` so the empty-dict fallback
works. Keep `_str_or_none()` as the single narrowing point — it already maps a
non-`str` value to `None`.

Do **not** add validation here (Decision 4): validation belongs at the point of
use (step 5) so `verify` can report every violation at once.

## DATA

On a mismatch every value degrades to `None`:

```python
{"default_provider": None, "backend": None, "model": None,
 "api_key": None, "base_url": None, "api_version": None}
```

Downstream, a `None` backend already produces the existing
`llm.langchain.backend not configured` error — an accurate message rather than a
traceback.

## TDD

1. Patch `get_config_values` to raise `ValueError` → `_load_langchain_config()`
   returns a dict of `None`s and does not raise; a warning is logged.
2. Happy path unchanged (existing tests must stay green).
3. End-to-end: `execute_verify` with a config whose `[llm.langchain] model` is an
   int completes and returns exit 1 from the *config* error, not a traceback.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`.
> Implement step 4: make `_load_langchain_config()` in
> `llm/providers/langchain/__init__.py` genuinely raise-free by catching the
> `ValueError` that `get_config_values` raises on a schema type mismatch, logging
> a warning and degrading every value to `None`. Do not add validation here.
> Write tests first (TDD), including a regression test that `mcp-coder verify`
> survives `[llm.langchain] model = 123` without a traceback.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
