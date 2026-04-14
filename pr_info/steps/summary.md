# Issue #792: Suppress false TERM warning on non-SSH terminals

## Problem
`_check_ssh_dumb_terminal` warns when `TERM` is `dumb` or unset, but this fires on Windows (VS Code) and local terminals where it's a false positive. The `export TERM=...` instruction is Linux-only syntax, confusing on Windows.

## Solution
Guard the check behind `SSH_CONNECTION` — only SSH sessions can have a genuinely dumb terminal that breaks TUI rendering. Rename the method and update the message for clarity.

## Architectural / Design Changes
- **No structural changes** — same class, same check pattern, same warning mechanism.
- **Behavioral change**: The existing TERM check becomes SSH-scoped. The method now returns early when `SSH_CONNECTION` is not set, eliminating false positives on all local terminals (Windows, macOS, Linux).
- **Naming change**: Method name shifts from `_check_ssh_dumb_terminal` → `_check_ssh_terminal_capabilities` to reflect the narrower SSH-only scope.

## Files Modified

| File | Action |
|------|--------|
| `src/mcp_coder/utils/tui_preparation.py` | Rename method, add SSH guard, update message |
| `tests/utils/test_tui_preparation.py` | Update test class/method names, add SSH_CONNECTION to fixtures, add guard test |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Update tests for renamed method and SSH guard | Tests + source changes together |
| 2 | Update integration test that exercises `run_all_checks` with TERM=dumb | Fix remaining test |
