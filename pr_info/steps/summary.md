# Summary: Fix session log files stored in target project instead of mcp-coder directory

## Problem
NDJSON session log files are created in `{execution_dir}/logs/claude-sessions/` — inside the **target project** — because `prompt_llm()` never passes `logs_dir` to `ask_claude_code_cli()`. The `get_stream_log_path()` function then defaults to `{cwd}/logs/`, polluting the target project.

## Design Decision: Extract `project_dir` from existing `env_vars`

Instead of the original issue proposal (add `project_dir` parameter to `prompt_llm()` + update ~17 call sites), we use a simpler approach:

**`env_vars` already contains `MCP_CODER_PROJECT_DIR`** — set by `prepare_llm_environment()` which every caller uses. We extract it inside `prompt_llm()` to derive `logs_dir`, requiring **zero caller changes**.

| Aspect | Original proposal | Simplified approach |
|---|---|---|
| Files changed (production) | 8 | 1 |
| New parameters | 1 on `prompt_llm` | 0 |
| Call sites updated | ~17 | 0 |
| Test impact | Signature changes ripple | Assertions updated for new kwarg |

## Architectural Change

```
BEFORE:
  callers → prompt_llm(execution_dir=X) → ask_claude_code_cli(cwd=X)
                                            → get_stream_log_path(cwd=X)
                                              → {X}/logs/claude-sessions/  ← WRONG

AFTER:
  callers → prompt_llm(env_vars={MCP_CODER_PROJECT_DIR: P}, execution_dir=X)
              ↓ extract P from env_vars
              → ask_claude_code_cli(cwd=X, logs_dir=P/logs)
                → get_stream_log_path(logs_dir=P/logs)
                  → {P}/logs/claude-sessions/  ← CORRECT
```

## Files Modified

| File | Change |
|---|---|
| `src/mcp_coder/llm/interface.py` | Extract `MCP_CODER_PROJECT_DIR` from `env_vars`, pass as `logs_dir` |
| `tests/llm/test_interface.py` | Add new tests for `logs_dir` derivation; update existing assertions |

## Files NOT Modified
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py` — already supports `logs_dir` parameter
- All 7 caller files — no signature changes needed
- No new files created

## Requirements Preserved
- Logs go to `{mcp_coder_project_dir}/logs/claude-sessions/`
- Fallback preserved: when `env_vars` is `None` or missing the key, `logs_dir=None` keeps existing default behavior
- No cleanup of existing stray files in target projects
- Backward compatible — no public API changes
