# Issue #740: Set DISABLE_AUTOUPDATER=1 when LLM invokes Claude CLI

## Problem

`prepare_llm_environment()` in `src/mcp_coder/llm/env.py` builds the env dict passed to every Claude CLI subprocess, but never sets `DISABLE_AUTOUPDATER=1`. The autoupdater only gets disabled when the parent shell happens to set it (e.g., via `.bat` launchers). Running `mcp-coder prompt` / `implement` / `icoder` from a plain shell leaves it active.

## Solution

Add one line to `prepare_llm_environment()`:

```python
env_vars["DISABLE_AUTOUPDATER"] = os.environ.get("DISABLE_AUTOUPDATER", "1")
```

This defaults to `"1"` (disabled) but respects any value the user has explicitly set in the parent environment.

## Architectural / Design Changes

- **No new modules, classes, or files** — this is a single-line addition to an existing function.
- **No change to function signatures or return type** — the dict already has `str` keys/values; we add one more entry.
- **Centralized control** — all callers of `prepare_llm_environment()` (icoder, prompt, implement, coordinator) automatically get the new variable. No per-caller changes needed.
- **Backward compatible** — callers that don't care about `DISABLE_AUTOUPDATER` are unaffected; callers that already set it in the parent env have their value preserved.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/env.py` | Add `DISABLE_AUTOUPDATER` to env dict in `prepare_llm_environment()` |
| `tests/llm/test_env.py` | Add 2 tests: default value and preserve-existing-value |

## Implementation Steps

| Step | Description |
|------|-------------|
| [Step 1](step_1.md) | Add tests and implementation for `DISABLE_AUTOUPDATER` in `prepare_llm_environment()` |
