# Issue #746 — Fix watchdog set-status missing --project-dir

## Problem

Watchdog `set-status` calls in Jenkins command templates fail on Windows because they lack `--project-dir`. When `resolve_project_dir()` defaults to `cwd`, it lands on the venv directory (e.g. `C:\Jenkins\environments\mcp-coder-dev`), which is not a git repository.

The main workflow commands (`create-plan`, `implement`, `create-pr`) already pass `--project-dir` correctly — only the watchdog `set-status` lines that follow them are missing it.

## Root Cause

In `command_templates.py`, all 6 watchdog `set-status` lines (3 Linux + 3 Windows) omit `--project-dir`.

## Fix — Template-Only Change

Add `--project-dir` to all 6 watchdog `set-status` lines:

- **Linux** (3 lines): `--project-dir /workspace/repo`
- **Windows** (3 lines): `--project-dir %WORKSPACE%\repo`

No logic changes. No new modules. No architectural changes.

## Architectural / Design Impact

**None.** This is a string-literal fix in command templates. The `set-status` command itself works correctly — the templates simply weren't passing the required argument.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | Add `--project-dir` to 6 watchdog `set-status` lines |
| `tests/cli/commands/coordinator/test_commands.py` | Add test asserting `--project-dir` is present in all 6 watchdog lines |

## Steps

| Step | Description |
|------|-------------|
| [Step 1](step_1.md) | Add TDD test + fix all 6 watchdog `set-status` lines |
