# Implementation Review Log — Run 1

**Issue:** #553 — mcp-coder verify: show contextual install instructions for active provider
**Date:** 2026-03-24

## Round 1 — 2026-03-24
**Findings**:
- C1: Scope creep — unrelated file deletions bundled in branch diff
- C2: `TestMcpServersInVerify` mocks `verify_claude` but langchain path calls `find_claude_executable` — incorrect mock targets
- S1: Non-pip install hints (Claude docs URL) dropped from summary block
- S2: Duplicate test fixture helpers across test files (pre-existing)
- S3: `_collect_install_hints` handling of `overall_ok` key (already correct)

**Decisions**:
- C1: **Skip** — False positive. Branch only modifies planned files (verified via `git diff merge-base..HEAD`). The unrelated files appear in `git diff main..HEAD` due to main advancing 6 commits since branch diverged. Needs rebase, not cleanup.
- C2: **Accept** — Real issue. Tests mock `verify_claude` but the langchain code path calls `find_claude_executable` instead. Bounded fix.
- S1: **Skip** — Intentional by design. Issue spec says summary shows `pip install ...`. Claude docs URL is rendered inline.
- S2: **Skip** — Pre-existing, out of scope per knowledge base ("pre-existing issues are out of scope").
- S3: **Skip** — Already handled correctly.

**Changes**:
- Fixed `tests/cli/commands/test_verify_exit_codes.py`: In `TestMcpServersInVerify`, replaced `@patch("...verify_claude")` with `@patch("...find_claude_executable", return_value=None)` in both tests. Renamed parameter, removed unnecessary mock setup.
- All checks pass: 2610 tests, pylint clean, mypy clean.

**Status**: committed
