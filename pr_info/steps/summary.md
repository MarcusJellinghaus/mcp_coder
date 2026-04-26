# Issue #885: install-from-github not auto-detected from pyproject.toml

## Problem

When vscodeclaude launches a session, `_build_github_install_section()` only runs when the `--install-from-github` CLI flag is passed (`install_from_github=True`). The function itself is already safe to call unconditionally — it returns `""` when no packages are configured. This means `[tool.mcp-coder.install-from-github]` in pyproject.toml is silently ignored.

## Design Changes

### Before (broken)
```
CLI --install-from-github flag
  → threaded as bool through ~8 function signatures
  → stored in VSCodeClaudeSession dict (persisted to disk)
  → guards _build_github_install_section() call in create_startup_script()
```

### After (fixed)
```
_build_github_install_section() always called (auto-detect from pyproject.toml)
CLI --no-install-from-github flag (opt-out escape hatch, not persisted)
  → threaded only through: CLI → commands.py → session_launch.py → workspace.py
```

### Key architectural decisions
- **Auto-detect by default**: `_build_github_install_section()` runs unconditionally — it's already idempotent
- **Opt-out replaces opt-in**: `--no-install-from-github` replaces `--install-from-github`
- **No session persistence**: `skip_github_install` is a one-shot flag, not stored in session dict. Restarts always auto-detect from pyproject.toml (correct — if config changed, you want current state)
- **Bulk deletion**: Most of the change is removing `install_from_github` plumbing from session state, `build_session()`, and ~8 function signatures

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/types.py` | Remove `install_from_github` from `VSCodeClaudeSession` |
| `src/mcp_coder/workflows/vscodeclaude/helpers.py` | Remove `install_from_github` param from `build_session()` |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Remove guard, rename param to `skip_github_install`, add cache comment |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | Rename param in `prepare_and_launch_session()`, `process_eligible_issues()`, `regenerate_session_files()` |
| `src/mcp_coder/workflows/vscodeclaude/session_restart.py` | Remove `install_from_github` from session reconstruction dict |
| `src/mcp_coder/cli/parsers.py` | Replace `--install-from-github` with `--no-install-from-github` |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Read new flag, pass as `skip_github_install` |

## Test Files Modified

| File | Change |
|------|--------|
| `tests/workflows/vscodeclaude/test_types.py` | Remove `install_from_github` from expected fields and session dicts |
| `tests/workflows/vscodeclaude/test_helpers.py` | Remove/rewrite `TestBuildSessionInstallFromGithub` class |
| `tests/workflows/vscodeclaude/test_workspace_startup_script_github.py` | Rewrite tests: auto-detect behavior, `skip_github_install` opt-out |
| `tests/workflows/vscodeclaude/test_session_launch.py` | Rewrite `TestInstallFromGithubThreading`: `skip_github_install` param, no session storage |
| `tests/workflows/vscodeclaude/test_session_launch_regenerate.py` | Remove `install_from_github` from session fixture |
| `tests/workflows/vscodeclaude/test_session_restart.py` | Remove `install_from_github` from session dicts |
| `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py` | Remove `install_from_github` from session dicts |
| `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` | Update 3 tests to use `--no-install-from-github` / `no_install_from_github` with opt-out semantics |
| `tests/cli/commands/coordinator/test_commands.py` | Update ~9 references: rename `install_from_github` to `skip_github_install` / `no_install_from_github` in parameter threading tests |
| `tests/workflows/vscodeclaude/test_cleanup.py` | Remove `"install_from_github": False` from ~39 session dict literals |
| `tests/workflows/vscodeclaude/test_status_display.py` | Remove `"install_from_github": False` from ~29 session dict literals |
| `tests/workflows/vscodeclaude/test_sessions.py` | Remove `"install_from_github": False` from ~22 session dict literals |
| `tests/workflows/vscodeclaude/test_session_restart_cache.py` | Remove `"install_from_github": False` from ~7 session dict literals |
| `tests/workflows/vscodeclaude/test_closed_issues_integration.py` | Remove `"install_from_github": False` from ~6 session dict literals |
| `tests/workflows/vscodeclaude/test_cache_aware.py` | Remove `"install_from_github": False` from ~4 session dict literals |
| `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py` | Remove `"install_from_github": False` from ~3 session dict literals |

## Implementation Order

1. **Step 1**: Remove `install_from_github` from session state (`types.py`, `helpers.py`) + `session_launch.py` `build_session()` call site + tests
2. **Step 2**: Fix the core bug in `workspace.py` (remove guard, rename param, add comment) + `session_launch.py` `create_startup_script()` call site kwargs + tests
3. **Step 3**: Update `session_launch.py` (rename function signature params, remove from `regenerate_session_files`) + tests
4. **Step 4**: Update `session_restart.py` (remove from session reconstruction) + tests
5. **Step 5**: Update CLI layer (`parsers.py`, `commands.py`) + tests
