# Implementation Review Log — Issue #987

CI branch-status: report missing GitHub token as a distinct `UNAVAILABLE` state.

Supervisor-driven review. Each round: engineer runs `/implementation_review`, supervisor triages, engineer implements accepted findings, commit agent commits.

---

## Round 1 — 2026-07-02

**Findings** (from `/implementation_review`):
1. [Suggestion] `--wait-for-pr` missing-token guard prints only the `CI Status:` line, not the full partial report (rebase + tasks) like the read-only/`--ci-timeout` paths do.
2. [Nitpick] Guard-path `print` of the 🔒 hint (`check_branch_status.py:161`) is not wrapped in the `UnicodeEncodeError` ascii-fallback that protects the main report print. On Windows cp1252 consoles it raises, is swallowed by the broad outer `except`, and the user loses the actionable hint.
3. [Nitpick] `get_github_token()` evaluated up to twice per invocation (CLI guard + `_collect_ci_status`).

Quality gates at review time: pylint clean, pytest 126 passed, mypy clean. No Critical findings.

**Decisions**:
- #1 **Skip** — intentional design (summary.md §3): `--wait-for-pr` exists to poll PRs, impossible without a token, so it fails cleanly with the hint rather than restructuring. Not a regression.
- #2 **Accept** — real robustness bug on the project's primary platform (Windows); a swallowed hint defeats the purpose of #987. Low effort, pattern already in file.
- #3 **Skip** — explicitly sanctioned by the issue as cheap and idempotent.

**Changes**:
- Extracted module-level `_safe_print(text)` helper (try/print → `UnicodeEncodeError` → ascii-replace fallback) in `check_branch_status.py`.
- Guard-path hint print and the main report print now both use `_safe_print` (DRY, identical behavior).
- Added `test_missing_token_wait_for_pr_hint_survives_unicode_error` (patches `print` to raise `UnicodeEncodeError`, asserts hint still reaches stdout and exit 2).
- Files: `src/mcp_coder/cli/commands/check_branch_status.py`, `tests/cli/commands/test_check_branch_status.py`.

**Status**: implemented; quality gates pass (pylint clean, pytest 12/12 on affected file, mypy clean). To be committed.

## Round 2 — 2026-07-02

**Findings**: none. Fresh review verified the round-1 `_safe_print` refactor: helper correct and well-placed, both call sites behavior-identical (guard path strictly improved), new Unicode-survival test is behavior-focused and not brittle, and the #987 design remains fully intact (UNAVAILABLE state, two-site `get_github_token()` detection, inline human+LLM hints, exit 2 on all paths, UNAVAILABLE excluded from ready-to-merge).

**Decisions**: n/a — nothing to accept or skip.

**Changes**: none.

Quality gates: pylint clean, mypy clean, pytest 4065 passed / 2 skipped / 0 failed.

**Status**: no changes needed — review loop converged.

---

## Final Status

**Rounds run**: 2 (round 1 → 1 accepted fix; round 2 → clean, loop converged).

**Code commits produced**: 1
- `9d66d21` — CLI: make missing-token guard print Unicode-safe via `_safe_print` helper.

**Supervisor checks**:
- `run_vulture_check`: no output (no dead code).
- `run_lint_imports_check`: PASSED — 19 contracts kept, 0 broken.

**Quality gates** (round 2, full suite): pylint clean, mypy clean, pytest 4065 passed / 2 skipped / 0 failed.

**Assessment**: Implementation is faithful to the #987 design and all gates are green. No open review items. Ready for PR review.
