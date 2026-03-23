# Issue #552: `mcp-coder verify` CONFIG Section

## Summary

Add a **CONFIG** section to `mcp-coder verify` that checks for the user config file (`config.toml`), validates it, and shows a summary of configured sections with environment variable detection.

## Architectural / Design Changes

### New Function: `verify_config()` in `utils/user_config.py`

A single new function that inspects the config file and returns a structured result dict. This keeps config verification logic next to the existing config utilities (`load_config`, `get_config_file_path`, etc.).

**Design decision**: `verify_config()` returns pure data (no formatting, no symbols). The formatting is handled inline in `execute_verify()` (~5 lines), avoiding a new formatter function. This is intentional — the CONFIG section's output format (bracket-prefixed labels, multi-line hints, dual-source annotations) doesn't fit `_format_section()` and creating a dedicated formatter for one call site adds complexity without benefit.

**Return structure**:
```python
{
    "entries": [
        {"label": "Config file", "status": "ok"|"warning"|"error", "value": "..."},
        {"label": "[llm]", "status": "ok", "value": "default_provider = langchain"},
        ...
    ],
    "has_error": bool  # True ONLY for invalid TOML → exit 1
}
```

### Modified: `_compute_exit_code()` in `cli/commands/verify.py`

One new parameter: `config_has_error: bool = False`. When `True`, returns exit code 1. Missing config does NOT affect exit code.

### Modified: `execute_verify()` in `cli/commands/verify.py`

CONFIG section is printed **first** (before BASIC VERIFICATION). Inline formatting loop maps `status` → symbol and prints each entry.

### No-op: `[llm] provider` key cleanup

Confirmed that `("llm", "provider")` does not exist anywhere in the codebase. Only `default_provider` is used. No cleanup needed.

## Environment Variables Checked

| Section | Env Var |
|---------|---------|
| `[github]` | `GITHUB_TOKEN` |
| `[jenkins]` | `JENKINS_URL`, `JENKINS_USER`, `JENKINS_TOKEN` |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/user_config.py` | Add `verify_config()` function |
| `src/mcp_coder/cli/commands/verify.py` | Import + call `verify_config()`, inline format CONFIG section, update `_compute_exit_code()` |
| `tests/utils/test_user_config.py` | Add `TestVerifyConfig` class |
| `tests/cli/commands/test_verify_exit_codes.py` | Add config_has_error exit code tests |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | `verify_config()` — tests + implementation in `user_config.py` | Tests + function |
| 2 | Integrate into `verify.py` — formatting, `_compute_exit_code`, `execute_verify` | Tests + wiring |
