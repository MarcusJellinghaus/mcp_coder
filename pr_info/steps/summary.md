# Adopt mcp-coder-utils (subprocess_runner + streaming + log_utils)

**Issue:** #744
**Branch:** `adopt/mcp-coder-utils`

## Goal

Replace full implementations of `subprocess_runner.py`, `subprocess_streaming.py`, and `log_utils.py` with thin re-export shims over `mcp-coder-utils`. Internal imports stay unchanged — zero churn across the codebase.

## Architectural / Design Changes

### Before
```
mcp_coder.utils.subprocess_runner   →  full implementation (~450 lines, imports subprocess directly)
mcp_coder.utils.subprocess_streaming →  full implementation (~160 lines, imports subprocess directly)
mcp_coder.utils.log_utils           →  full implementation (~350 lines, imports structlog + pythonjsonlogger directly)
```

### After
```
mcp_coder.utils.subprocess_runner   →  thin shim re-exporting from mcp_coder_utils.subprocess_runner
mcp_coder.utils.subprocess_streaming →  thin shim re-exporting from mcp_coder_utils.subprocess_streaming
mcp_coder.utils.log_utils           →  thin shim re-exporting from mcp_coder_utils.log_utils + mcp_coder_utils.redaction
                                        + wrapped setup_logging() with app-specific third-party log suppression
```

### Dependency flow change
```
Before:  mcp_coder.utils.subprocess_runner  →  subprocess (stdlib)
         mcp_coder.utils.subprocess_streaming → subprocess (stdlib)
         mcp_coder.utils.log_utils          →  structlog, pythonjsonlogger

After:   mcp_coder.utils.subprocess_runner  →  mcp_coder_utils.subprocess_runner
         mcp_coder.utils.subprocess_streaming → mcp_coder_utils.subprocess_streaming
         mcp_coder.utils.log_utils          →  mcp_coder_utils.log_utils, mcp_coder_utils.redaction
         (no more direct structlog/pythonjsonlogger/subprocess imports in shims)
```

### Import-linter boundary changes
- **New contract:** `mcp_coder_utils_isolation` — only the 3 shim files may import `mcp_coder_utils`
- **Tightened:** `structlog_isolation` — remove `log_utils` exception (shim doesn't import structlog)
- **Tightened:** `jsonlogger_isolation` — remove `log_utils` exception (shim doesn't import pythonjsonlogger)
- **Updated:** `subprocess_isolation` — shim files no longer import `subprocess` directly; remove those exceptions, remove deleted test file exceptions

### stream_subprocess API change
- Old: `stream_subprocess(command, options)` returns `Generator`, caller wraps in `StreamResult()`
- New: `stream_subprocess(command, options, inactivity_timeout_seconds=None)` returns `StreamResult` directly
- Caller (`claude_code_cli_streaming.py`) drops manual wrapper, passes timeout as kwarg

### Test ownership shift
- 5 test files deleted (tests now live in mcp-coder-utils)
- 1 new test added: verifies the log suppression shim works

## Files Modified

| File | Action |
|------|--------|
| `pyproject.toml` | Modify — pin `mcp-coder-utils>=0.1.3` |
| `src/mcp_coder/utils/subprocess_runner.py` | Modify — replace body with re-export shim |
| `src/mcp_coder/utils/subprocess_streaming.py` | Modify — replace body with re-export shim |
| `src/mcp_coder/utils/log_utils.py` | Modify — replace body with re-export shim + wrapped `setup_logging()` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` | Modify — adapt to new `stream_subprocess` API |
| `.importlinter` | Modify — add `mcp_coder_utils_isolation`, update 3 existing contracts |
| `.claude/CLAUDE.md` | Modify — add shared-libraries note |
| `tests/utils/test_subprocess_runner.py` | Delete |
| `tests/utils/test_subprocess_runner_real.py` | Delete |
| `tests/utils/test_subprocess_streaming.py` | Delete |
| `tests/utils/test_log_utils.py` | Delete |
| `tests/utils/test_log_utils_redaction.py` | Delete |
| `tests/utils/test_log_utils_shim.py` | Create — log suppression shim test |

## Pre-merge prerequisite

`mcp-coder-utils` 0.1.3 must be published to PyPI before this PR merges.

## Steps Overview

1. **Dependency + subprocess shims** — `pyproject.toml`, `subprocess_runner.py`, `subprocess_streaming.py`
2. **log_utils shim** — `log_utils.py` with wrapped `setup_logging()`
3. **stream_subprocess API update** — `claude_code_cli_streaming.py`
4. **Import-linter contracts** — `.importlinter` (all contract changes)
5. **Test cleanup + shim test** — delete 5 test files, add `test_log_utils_shim.py`
6. **Docs + stale import grep** — CLAUDE.md one-liner, verify no stale imports
