# Issue #887 — docs: update CLAUDE.md shared libraries section

## Summary

Replace the current single-paragraph "Shared Libraries" section in `.claude/CLAUDE.md` with an expanded version that gives the LLM full awareness of the mcp-coder-utils dependency: a table of shim→upstream mappings with key imports, a "do not reimplement" rule, and a pointer to the `p_coder-utils` reference project.

## Architectural / Design Changes

**None.** This is a documentation-only change. No code, tests, types, or runtime behaviour are affected.

The change improves LLM session quality by ensuring Claude always has context about:
- Which utilities exist in `mcp-coder-utils` (preventing reimplementation)
- How to look up the full source via the reference project mechanism
- The import-linter enforcement rule (existing, just better documented)

## Files Modified

| File | Change |
|------|--------|
| `.claude/CLAUDE.md` | Replace `## Shared Libraries` section (lines 103–105) with expanded table + rules |

No files created. No files deleted.

## Implementation

Single step — see `step_1.md`.
