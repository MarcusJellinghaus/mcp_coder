# Issue #670: Clean CLI output — OUTPUT-level formatter + print migration

## Problem
`mcp-coder` CLI commands produce verbose logging output (timestamps, module names, level prefixes) that is hard to parse programmatically. Additionally, `print()` statements bypass the logging system inconsistently.

## Solution Overview
Rename the existing `NOTICE` (25) custom log level to `OUTPUT` (25) and introduce a dual-formatter design where the log **threshold** controls the **formatter**:

| Threshold | Formatter | Use case |
|-----------|-----------|----------|
| `OUTPUT` (default) | `CleanFormatter`: `%(message)s` for OUTPUT; `WARNING: %(message)s` for higher | CLI callers, automation |
| `INFO` / `DEBUG` | `ExtraFieldsFormatter`: `%(asctime)s - %(name)s - %(levelname)s - %(message)s` | Interactive debugging |

## Architectural / Design Changes

### 1. Dual-formatter logging design (`log_utils.py`)
- **New `CleanFormatter` class** — standalone (does NOT inherit `ExtraFieldsFormatter`). Independently implements extra-fields JSON appending. For OUTPUT-level records: bare `%(message)s`. For WARNING/ERROR/CRITICAL: `LEVEL: %(message)s`.
- **`ExtraFieldsFormatter`** — unchanged, used when threshold is INFO or DEBUG.
- **`setup_logging()`** — selects formatter based on threshold: OUTPUT → `CleanFormatter`, else → `ExtraFieldsFormatter`.
- **Clean rename**: `NOTICE` constant/level → `OUTPUT`. No backward-compatible alias.

### 2. Default threshold change (`cli/main.py`)
- All commands default to `OUTPUT` threshold (previously: workflow commands defaulted to `INFO`, others to `NOTICE`).
- Exception: `coordinator` command keeps `INFO` default (it sets `--log-level INFO` when invoking sub-commands).
- `OUTPUT` added to `--log-level` CLI choices.

### 3. `create-pr` workflow cleanup (`workflows/create_pr/core.py`)
- `log_step()` helper removed entirely.
- All call sites replaced with `logger.log(OUTPUT, ...)`, keeping "Step N/5:" prefix.
- PR summary fields logged at OUTPUT level after creation (number, URL, title, base, head).
- Detail messages stay at `logger.info()` — invisible at OUTPUT threshold.

### 4. Print migration (CLI commands)
- `print("Error: ...", file=sys.stderr)` → `logger.error(...)`
- `print("status message")` → `logger.log(OUTPUT, ...)`
- **Keep `print()` for data output**: help text, compact-diff, branch-status report tables, JSON output, `verify` command formatted sections, `vscodeclaude status` table.
- Scope: `cli/main.py`, `cli/commands/*.py` (including `coordinator/commands.py` for vscodeclaude prints).

### 5. CI wait progress (`check_branch_status.py`)
- Replace `print(".", end="", flush=True)` dot pattern with periodic `logger.log(OUTPUT, ...)` messages (~60s interval).
- 15s poll interval unchanged.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/log_utils.py` | Rename NOTICE→OUTPUT, add `CleanFormatter`, update `setup_logging()` |
| `src/mcp_coder/utils/__init__.py` | Rename `NOTICE` export → `OUTPUT` |
| `src/mcp_coder/cli/main.py` | Update `--log-level` choices, `_INFO_COMMANDS`, `_resolve_log_level()` default |
| `src/mcp_coder/workflows/create_pr/core.py` | Remove `log_step()`, use `logger.log(OUTPUT, ...)`, add PR summary fields |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Replace dot-progress with periodic OUTPUT messages |
| `src/mcp_coder/cli/commands/commit.py` | Migrate status/error prints to logging |
| `src/mcp_coder/cli/commands/create_pr.py` | Migrate error prints to logging |
| `src/mcp_coder/cli/commands/create_plan.py` | Migrate error prints to logging |
| `src/mcp_coder/cli/commands/implement.py` | Migrate error prints to logging |
| `src/mcp_coder/cli/commands/init.py` | Migrate status prints to logging |
| `src/mcp_coder/cli/commands/prompt.py` | Migrate status/error prints to logging (keep data prints) |
| `src/mcp_coder/cli/commands/set_status.py` | Migrate status/error prints to logging (keep label listing) |
| `src/mcp_coder/cli/commands/gh_tool.py` | Migrate error prints to logging (keep data prints) |
| `src/mcp_coder/cli/commands/git_tool.py` | Migrate error prints to logging (keep data print) |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Migrate status/error prints to logging |
| `tests/utils/test_log_utils.py` | Rename NOTICE→OUTPUT tests, add `CleanFormatter` tests |
| `tests/cli/test_main.py` | Update NOTICE→OUTPUT references |

## Files NOT Modified (data-producing prints kept as-is)
- `src/mcp_coder/cli/commands/help.py` — `print(help_text)` is data output
- `src/mcp_coder/cli/commands/verify.py` — `print()` outputs formatted verification report (data)
- `src/mcp_coder/workflows/vscodeclaude/status.py` — `print(tabulate(...))` is data output

## Implementation Steps

1. **Step 1**: Logging infrastructure — NOTICE→OUTPUT rename, `CleanFormatter`, `setup_logging()` update, tests
2. **Step 2**: CLI defaults — `--log-level` choices, `_resolve_log_level()`, `_INFO_COMMANDS`
3. **Step 3**: `create-pr` workflow — remove `log_step()`, add PR summary fields
4. **Step 4**: CI wait progress and check_branch_status print migration
5. **Step 5**: Print migration across CLI commands — status/error prints to logging
6. **Step 6**: Print migration for coordinator and remaining commands
