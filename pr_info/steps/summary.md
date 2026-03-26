# Issue #595: set-status — show available labels when called without args

## Problem

`mcp-coder gh-tool set-status` requires a `status_label` argument. If omitted, argparse shows a generic error. Users shouldn't need to fail to discover available options.

## Solution Overview

Make `status_label` optional. When omitted, print a formatted table of available status labels and exit 0. Unify all label-formatting code into a single `format_status_labels()` function used by: no-args output, `--help` epilog, and invalid-label error message.

## Architectural / Design Changes

### New function: `format_status_labels(labels_config: dict) -> str`
- **Location**: `src/mcp_coder/cli/commands/set_status.py`
- **Purpose**: Single source of truth for rendering the label table
- **Design**: Takes a loaded config dict (does not load config itself). Computes dynamic column width from `max(len(label["name"]))` so the table adapts if labels are renamed/added.

### Signature change: `validate_status_label(label, labels_config)` 
- **Was**: `validate_status_label(label: str, valid_labels: set[str])`
- **Now**: `validate_status_label(label: str, labels_config: dict)`
- **Why**: Needs the full config to call `format_status_labels()` for the error message. Only one caller (`execute_set_status`), which already loads the config.

### Argparse change: `status_label` becomes optional
- **Was**: required positional argument
- **Now**: `nargs="?"`, `default=None`
- **Effect**: `set-status` without args no longer errors from argparse

### No-args early return in `execute_set_status()`
- Skips clean-dir check, issue resolution, and GitHub API calls — purely informational
- Best-effort project dir: tries `resolve_project_dir()` for local label overrides, falls back to bundled config via `get_labels_config_path(None)` on failure

## Behavior Matrix

| Invocation | Output | Exit code |
|---|---|---|
| `set-status` (no args) | Label table | 0 |
| `set-status --help` | Help text with label table in epilog | 0 |
| `set-status valid-label` | Updates issue label | 0 |
| `set-status invalid-label` | Error + label table | 1 |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | Make `status_label` optional (`nargs="?"`, `default=None`) |
| `src/mcp_coder/cli/commands/set_status.py` | Add `format_status_labels()`, refactor `build_set_status_epilog()` and `validate_status_label()` to use it, add no-args path in `execute_set_status()`, update docstring |
| `tests/cli/commands/test_set_status.py` | Add no-args test, update `validate_status_label` tests for new signature |

## Implementation Steps

1. **Step 1** — Add `format_status_labels()` + refactor `build_set_status_epilog()` and `validate_status_label()` to use it. Update tests for changed signatures.
2. **Step 2** — Make `status_label` optional in parser, add no-args early return in `execute_set_status()`, add no-args test, update docstring.
