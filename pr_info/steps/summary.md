# Issue #625: Improve message when no previous sessions found

## Summary

When using `--continue-session` without a prior `--store-response`, the CLI prints a message that doesn't guide the user on how to fix it. This change appends actionable guidance to the existing message.

## Architectural / Design Changes

**None.** This is a single string literal change. No new modules, classes, functions, or control flow changes are introduced.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/commands/prompt.py` | Update message string on line 99 |
| `tests/cli/commands/test_prompt_continue_session_message.py` | New test asserting the improved message text |

## Folders / Modules Created

| Path | Purpose |
|------|---------|
| `pr_info/steps/` | Implementation plan documents (this PR) |

## Implementation Overview

- **Step 1**: Add a test for the improved message, then change the string. One commit.
