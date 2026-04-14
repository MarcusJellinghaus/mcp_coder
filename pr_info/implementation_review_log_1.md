# Implementation Review Log — Issue #808

**Issue:** iCoder: token usage + version in status line
**Branch:** 808-icoder-token-usage-version-in-status-line
**Review started:** 2026-04-14

## Round 1 — 2026-04-14

**Findings:**
1. `format_token_count()` doesn't handle negative numbers (types.py:44)
2. Token display not updated on error/cancel paths (app.py:155-170)
3. Doc says `mcp-coder <version>` but code renders `v{version}` (icoder.md)
4. Initial zeroes visible then hidden after first stream without usage data
5. No test for billions branch in `format_token_count()`
6. Missing async UI tests for `_update_token_display()`
7. Billions formatting uses integer division vs float for k/M
8. Version centering shifts when tokens hidden

**Decisions:**
- #1 Skip — token counts always non-negative, speculative fix
- #2 Skip — known decision from plan review, error paths stay simple
- #3 Accept — real doc/code mismatch, quick fix
- #4 Skip — intentional design (decisions #6/#11)
- #5 Skip — unrealistic input, low value
- #6 Skip — core logic well-tested, Textual async tests heavy for marginal coverage
- #7 Skip — unrealistic input range
- #8 Skip — cosmetic

**Changes:** Fixed version format in `docs/icoder/icoder.md` from `mcp-coder <version>` to `v<version>`
**Status:** Committed (ba10020)

## Round 2 — 2026-04-14

**Findings:** None
**Decisions:** N/A
**Changes:** None
**Status:** No changes needed

## Final Status

- **Rounds:** 2
- **Commits:** 1 (ba10020 — doc version format fix)
- **All quality checks pass:** pylint clean, mypy clean, 3564 tests passing
- **No remaining issues**
