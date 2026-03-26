# Summary: Unify CLI help, add NOTICE log level, move set-status to gh-tool

**Issue:** #591

## Goal

Three CLI improvements: (1) unified help output across all help paths, (2) custom NOTICE log level with per-command defaults to reduce noise, (3) move `set-status` under `gh-tool`.

## Architectural / Design Changes

### 1. Help System Consolidation

**Before:** Three different help outputs (`mcp-coder` → compact, `mcp-coder help` → detailed, `mcp-coder --help` → argparse flat list).

**After:** All three paths produce identical categorized output with version header and OPTIONS section. Achieved by `add_help=False` on the root parser + `--help`/`-h` as `store_true` args that route to the same `get_help_text()` function. Subparsers keep their `--help` intact.

### 2. NOTICE Log Level (25)

**Before:** All commands default to INFO, producing log noise for simple tool commands.

**After:** Custom NOTICE level (25) registered in Python logging. Workflow commands (`create-plan`, `implement`, `create-pr`, `coordinator`, `vscodeclaude launch`) default to INFO. All other commands default to NOTICE. User-facing progress messages are promoted to NOTICE; operational chatter stays at INFO (hidden at NOTICE level). `--log-level` always overrides; NOTICE is not exposed as a `--log-level` choice.

### 3. set-status → gh-tool set-status

**Before:** `mcp-coder set-status` is a top-level command.

**After:** `mcp-coder gh-tool set-status` — grouped with other GitHub operations. Hard removal, no deprecation shim.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | Move set-status parser into gh-tool; remove `add_set_status_parser()` |
| `src/mcp_coder/cli/main.py` | Remove top-level set-status route; add to `_handle_gh_tool_command`; add `add_help=False` + `--help` store_true; change `--log-level` default to `None`; add `_resolve_log_level()` |
| `src/mcp_coder/cli/commands/help.py` | Unified output: version header, OPTIONS section, remove `help` entry, remove `get_compact_help_text()`, rename `set-status` → `gh-tool set-status` |
| `src/mcp_coder/cli/commands/set_status.py` | Update epilog examples to `mcp-coder gh-tool set-status` |
| `src/mcp_coder/utils/log_utils.py` | Register NOTICE level (25), add `Logger.notice()` method |
| `.claude/commands/plan_approve.md` | `mcp-coder set-status` → `mcp-coder gh-tool set-status` |
| `.claude/commands/implementation_approve.md` | Same |
| `.claude/commands/implementation_needs_rework.md` | Same |
| `docs/processes-prompts/development-process.md` | Same |
| `docs/cli-reference.md` | Add `gh-tool set-status` section |

## Files Modified (Tests)

| File | Change |
|------|--------|
| `tests/cli/commands/test_help.py` | Update for unified help format, new command list, version/OPTIONS |
| `tests/cli/test_main.py` | Update for `--log-level` default change, `--help` routing, set-status removal |
| `tests/utils/test_log_utils.py` | Add NOTICE level registration test |

## Decisions

- **No deprecation shim for `set-status`** — hard removal.
- **`add_help=False` on root parser only** — subparsers keep `--help`.
- **`--help` implemented as `store_true` argument** — avoids sys.argv parsing complexity.
- **`--log-level` default is `None`** — enables clean detection of "user didn't provide it" vs "user explicitly set it". Per-command default resolved in `_resolve_log_level()`.
- **NOTICE not exposed as `--log-level` choice** — internal only.
- **Implementation order:** Part 3 (set-status move) → Part 2 (NOTICE level) → Part 1 (unified help) — each step builds cleanly on the previous.
