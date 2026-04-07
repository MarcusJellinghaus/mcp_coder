# Summary: Coordinator Template Watchdog + `--from-status` for Silent-Death Recovery

**Issue:** #713  
**Related:** #710 (silent death), #712 (crash instrumentation)

## Problem

When `mcp-coder implement` (or `create-plan`, `create-pr`) dies silently — no Python cleanup, no exception, no `finally` block — the GitHub issue stays stuck at its in-progress status label indefinitely (`status-06:implementing`, `status-03:planning`, `status-09:pr-creating`). Python's `_handle_workflow_failure()` cannot run in this scenario.

## Solution

An **outer watchdog** in the Jenkins shell templates that runs `set-status` unconditionally after the main command, using a new `--from-status` precondition flag to only apply a failure label if the issue is still stuck at the in-progress label.

## Architecture / Design Changes

### 1. New `--from-status LABEL` flag on `gh-tool set-status`

- **What:** A precondition guard on the existing `set-status` CLI command. Reads the issue's current status label; if it matches `--from-status`, applies the new label. Otherwise, no-op (exit 0, OUTPUT-level skip message).
- **Where:** `src/mcp_coder/cli/gh_parsers.py` (parser), `src/mcp_coder/cli/commands/set_status.py` (logic).
- **Design:** The check is added inside `_update_issue_labels()` — reusing the existing `get_issue()` call (no extra GitHub API round-trip). The `--from-status` value is validated against `labels.json` the same way the positional `status_label` is.
- **No new modules or classes.** This is a small addition to the existing command.

### 2. Updated coordinator Jenkins command templates

- **What:** All six workflow templates (`CREATE_PLAN_COMMAND_TEMPLATE`, `IMPLEMENT_COMMAND_TEMPLATE`, `CREATE_PR_COMMAND_TEMPLATE` + Windows variants) get: RC capture → watchdog `set-status` line → archive block → explicit exit with captured RC.
- **Where:** `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- **Design:** The watchdog runs unconditionally (not gated on exit code). It is a cheap no-op when the label has already transitioned. An inline comment block near the Linux templates serves as the source of truth for the recovery matrix.
- **No structural changes to the template system.** Only the string content of existing constants changes.

### Recovery Matrix (from issue)

| Exit path | Watchdog action |
|---|---|
| Clean success (label already past in-progress) | no-op (skip message) |
| Graceful failure (Python set specific failure label) | no-op (preserves specificity) |
| **Silent death** (issue still at in-progress label) | **rescues → generic `*-failed` label** |
| Hard kill of shell process | not recoverable (out of scope) |

## Files Modified

| File | Change |
|---|---|
| `src/mcp_coder/cli/gh_parsers.py` | Add `--from-status` argument to set-status parser |
| `src/mcp_coder/cli/commands/set_status.py` | Validate `--from-status`, precondition check in `_update_issue_labels` |
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | Update all 6 templates + inline recovery matrix comment |
| `tests/cli/commands/test_set_status.py` | Tests for `--from-status` flag |
| `tests/cli/commands/coordinator/test_commands.py` | Tests for template watchdog lines |

No new files or modules created.

## Implementation Steps

1. **Step 1** — `--from-status` flag: tests + implementation in `set_status.py` and `gh_parsers.py`
2. **Step 2** — Coordinator template watchdog: tests + template updates in `command_templates.py`
