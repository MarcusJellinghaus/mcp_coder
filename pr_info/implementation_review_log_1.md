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

## Round 2 — 2026-03-24
**Findings**:
- CRITICAL-1: `_collect_install_hints` brittle guard against `overall_ok` being a dict
- CRITICAL-2: Non-pip hints (Claude docs URL) silently dropped from summary / dead code path for Claude results
- S1: Hardcoded 27-space indentation in `_format_section` hint line
- S2: Duplicate test `test_cli_not_found_has_install_hint` — identical to updated `test_cli_not_found`
- S3: Duplicate `@patch` decorator stacks in orchestration tests

**Decisions**:
- CRITICAL-1: **Skip** — `isinstance(entry, dict)` guard is sufficient. Speculative concern about future changes.
- CRITICAL-2: **Skip** — No functional bug. `_collect_install_hints` on Claude results returns empty list harmlessly.
- S1: **Skip** — Cosmetic. Label width is stable.
- S2: **Accept** — Genuine redundancy. Removed duplicate test.
- S3: **Skip** — Consistent with existing test style.

**Changes**:
- Removed duplicate `test_cli_not_found_has_install_hint` from `tests/llm/providers/claude/test_claude_cli_verification.py`
- All checks pass: 2609 tests, pylint clean, mypy clean.

**Status**: committed

## Round 3 — 2026-03-24
**Findings**:
- S1: `_collect_install_hints` uses `not entry.get("ok")` which also matches `None`
- S2: Non-pip hints dropped from summary (repeat of Round 2)
- S3: Duplicate test helpers across files (repeat of Round 2)

**Decisions**:
- S1: **Skip** — No entries carry `install_hint` with `ok=None`. Speculative.
- S2: **Skip** — Already triaged in Round 2. Intentional by design.
- S3: **Skip** — Pre-existing, out of scope.

**Changes**: None
**Status**: no changes needed

## Final Status

**Rounds**: 3
**Commits produced**: 2 (fix mock targets, remove duplicate test)
**Remaining issues**: None
**Branch status**: CI passing, 6 commits behind base — needs rebase before merge.
