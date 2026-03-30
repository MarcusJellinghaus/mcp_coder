# Issue #635: gh-tool set-status — print success confirmation to stdout

## Problem

`mcp-coder gh-tool set-status <label>` returns exit code 0 on success but produces
no stdout output. Only a `logger.info()` call exists, which is invisible at default
log levels. LLM callers see `(No output)` and cannot confirm the operation succeeded.

## Solution

Add a single `print()` call on the success path in `execute_set_status()`, alongside
the existing `logger.info()`. Update existing success-path tests to assert stdout
content.

## Architectural / Design Changes

**None.** This is a one-line behavioral fix with no structural, architectural, or
design changes. The existing patterns (print to stdout for user-visible output, 
`logger.info()` for structured logging, print to stderr for errors) are already
established in the same function. We simply extend the success path to match the
pattern used everywhere else.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/commands/set_status.py` | Add `print()` on success path (1 line) |
| `tests/cli/commands/test_set_status.py` | Add `capsys` + stdout assertion to 4 success tests |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Update tests to expect stdout output on success (TDD: red) | Tests + prod fix + green |

This is small enough for a single step. The test changes and the one-line fix
are tightly coupled and trivial to review together.
