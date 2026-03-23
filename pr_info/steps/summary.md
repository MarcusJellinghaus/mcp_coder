# Issue #542: Add --llm-method claude to vscodeclaude workspace scripts

## Problem

VSCodeClaude Windows scripts use a two-phase workflow:
1. **Automated phase**: `mcp-coder prompt` creates a session
2. **Interactive phase**: `claude --resume %SESSION_ID%` resumes it

Issue #528 removed `--llm-method claude` from templates, deferring to config-based resolution. But if the user's config has `[llm] default_provider = langchain`, the automated phase creates a langchain session. The interactive phase then calls `claude --resume`, which only sees Claude-created sessions — causing "No conversation found" errors.

## Root Cause

The `claude --resume` command is inherently Claude-specific. The automated `mcp-coder prompt` step that creates the session must also use Claude, so the session IDs are compatible.

## Solution

Add `--llm-method claude` back to the two automated Windows templates that use `mcp-coder prompt`. No changes to interactive templates (they call `claude` CLI directly and don't use `mcp-coder prompt`).

## Architectural / Design Changes

- **No architectural changes.** This is a targeted fix to two template strings.
- The design principle reinforced: when a downstream step is provider-specific (`claude --resume`), the upstream step must match that provider explicitly rather than relying on config resolution.

## Scope

- **Windows templates only** — no Linux templates use `mcp-coder prompt`
- **No changes** to `resolve_llm_method()` or config resolution logic

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Add `--llm-method claude` to `AUTOMATED_SECTION_WINDOWS` and `AUTOMATED_RESUME_SECTION_WINDOWS` |
| `tests/workflows/vscodeclaude/test_templates.py` | Flip 2 automated tests to assert `mcp-coder prompt` and `--llm-method claude` ARE present; keep 2 interactive tests unchanged |

## Implementation Steps

- **Step 1**: Update tests and templates (single commit — all changes are tightly coupled)
