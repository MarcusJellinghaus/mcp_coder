# Issue #684: Rename `from-github` to `install-from-github`

## Summary

Rename the `from-github` / `from_github` identifier to `install-from-github` / `install_from_github` across all layers (config, CLI, Python internals) for clarity. Clean break — no backwards compatibility shims.

## Architectural / Design Changes

**None.** This is a pure rename with no structural, behavioral, or architectural changes. The data flow, control flow, and module boundaries remain identical:

```
CLI flag → coordinator commands → session_launch → workspace/helpers → pyproject.toml config
                                                 → session dict (TypedDict) → session_restart
```

The only change is the identifier name at each point in this chain.

## Files to Modify

| File | Change |
|------|--------|
| `pyproject.toml` | Config section `[tool.mcp-coder.from-github]` → `[tool.mcp-coder.install-from-github]` |
| `src/mcp_coder/cli/parsers.py` | CLI flag `--from-github` → `--install-from-github` |
| `src/mcp_coder/workflows/vscodeclaude/types.py` | TypedDict field `from_github` → `install_from_github` |
| `src/mcp_coder/workflows/vscodeclaude/helpers.py` | `build_session()` parameter + dict key |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | `create_startup_script()` parameter + TOML lookup string + `_build_github_install_section()` docstring |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | Parameters in `prepare_and_launch_session()`, `process_eligible_issues()`, `regenerate_session_files()` |
| `src/mcp_coder/workflows/vscodeclaude/session_restart.py` | Dict key in `restart_closed_sessions()` |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | `getattr(args, ...)` calls + keyword args (2 occurrences) |
| `tests/test_pyproject_config.py` | Config key reference in test assertion |

## Files to Create

None.

## Implementation Strategy

**2 steps, 2 commits:**

1. **Step 1** — Update the test to expect the new name (TDD: test goes red)
2. **Step 2** — Rename everything in source + config (test goes green)

This keeps it simple: one test commit, one implementation commit.
