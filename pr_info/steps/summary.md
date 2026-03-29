# Issue #618: fix: launch_process() env inheritance + add env_remove to CommandOptions

## Problem

Subprocess utility functions handle environment variables inconsistently:

1. **`launch_process()`** passes `env` directly to `subprocess.Popen` — if a caller passes a partial dict, the subprocess loses ALL parent env vars (PATH, HOME, etc.)
2. **`CLAUDECODE` env var removal** is hardcoded in `_run_subprocess` and `stream_subprocess` — should be caller-controlled
3. **Env setup logic is duplicated** in 3 places (`_run_subprocess`, `stream_subprocess`, `launch_process`)
4. **Utility functions** (`check_tool_missing_error`, `truncate_stderr`) exist in p_tools reference but are missing from this leading repo

## Architectural / Design Changes

### Before (current state)
```
_run_subprocess()      → inline: is_python? isolation_env : utf8_env + merge + hardcoded CLAUDECODE pop
stream_subprocess()    → inline: is_python? isolation_env : utf8_env + merge + hardcoded CLAUDECODE pop
launch_process()       → passes env directly to Popen (BUG: no inheritance)
```

### After (target state)
```
_prepare_env(command, env, env_remove)   ← NEW shared helper (single source of truth)
    ├── is_python_command? → get_python_isolation_env()
    ├── else              → get_utf8_env()
    ├── merge caller env on top
    └── remove env_remove keys

_run_subprocess()      → calls _prepare_env(command, options.env, options.env_remove)
stream_subprocess()    → calls _prepare_env(command, options.env, options.env_remove)
launch_process()       → calls _prepare_env(command, env, env_remove)

CommandOptions         → gains env_remove: list[str] | None = None
Claude CLI callers     → pass env_remove=["CLAUDECODE"] via CommandOptions
```

Key design decisions:
- `_prepare_env` is module-private (not exported) — it's an implementation detail
- `launch_process()` keeps individual params (not CommandOptions) — most CommandOptions fields don't apply to fire-and-forget
- CLAUDECODE removal moves from hardcoded to caller-controlled via `env_remove`

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_coder/utils/subprocess_runner.py` | Add `_prepare_env` helper, `env_remove` on `CommandOptions`, fix `launch_process`, add `check_tool_missing_error`/`truncate_stderr`/`MAX_STDERR_IN_ERROR` |
| `src/mcp_coder/utils/subprocess_streaming.py` | Use `_prepare_env` instead of inline env logic, import it |
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Add `env_remove=["CLAUDECODE"]` to `CommandOptions` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` | Add `env_remove=["CLAUDECODE"]` to `CommandOptions` |
| `tests/utils/test_subprocess_runner.py` | Add tests for `_prepare_env`, `env_remove`, `launch_process` env fix, merged utilities, integration test |

## No New Files Created

All changes go into existing files.

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | `_prepare_env` helper + `env_remove` on `CommandOptions` + tests | Tests + implementation for core helper |
| 2 | Refactor `_run_subprocess` and `stream_subprocess` to use `_prepare_env`; update Claude CLI callers with `env_remove=["CLAUDECODE"]` | Wire up the new helper everywhere |
| 3 | Fix `launch_process()` env inheritance + tests (unit + integration) | Fix the main bug |
| 4 | Merge `check_tool_missing_error`, `truncate_stderr`, `MAX_STDERR_IN_ERROR` from p_tools + tests | Port missing utilities |
