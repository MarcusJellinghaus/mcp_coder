# Plan Review Log — Issue #987 (Run 1)

Report missing GitHub token as a distinct CI `UNAVAILABLE` state.

Supervisor: technical lead delegating to engineer subagents (`/plan_review`, `/plan_update`).
Base branch: `main` (branch up to date, no rebase needed). Plan is fresh — no steps complete.

## Round 1 — 2026-07-02

**Findings** (from `/plan_review` engineer):
- CRITICAL C1: Step 2 adds `get_github_token` to `__all__` but doesn't update the `test_all_exports_defined` smoke assertion (`len(__all__) == 24`), so Step 2's pytest gate would fail.
- IMPROVEMENT I1: Step 2 cited wrong tests needing a dummy-token patch (line ~292 is a false positive; the real ones — `test_collect_ci_status_with_truncation` ~900, `_no_truncation` ~935, `_error_handling` ~953/964 — were mis/under-cited).
- DESIGN D1: `--fix` + no token returns exit 0 (not 2) because `UNAVAILABLE` isn't `FAILED`, so `_run_auto_fixes` short-circuits before the exit-code line.
- DESIGN D2: `--wait-for-pr` + no token exits 2 with no printed report (silent), via `PullRequestManager` raising into the outer except.
- LGTM: core design verified accurate against real code (`CIStatus` str-Enum, ready-to-merge gate `[PASSED, NOT_CONFIGURED]`, `_collect_ci_status` construction point, `format_for_human/llm` render points, shim + `get_github_token` from `mcp_workspace.config`, test layout, step ordering).

**Decisions**:
- C1 — accept (supervisor): bump smoke assertion 24→25 in Step 2.
- I1 — accept (supervisor): correct affected-test citations to the three tests that call `_collect_ci_status`.
- D1 — escalated → user chose **A**: hoist `UNAVAILABLE → 2` before the `--fix` block for consistent exit 2.
- D2 — escalated → user: `--wait-for-pr` must still FAIL (exit 2) on missing token, but cleanly with the actionable hint instead of a silent exit. Gate the path proactively.

**User decisions**: Q1=A (hoist exit-2 before `--fix`). Q2=gate `--wait-for-pr` on missing token → print `GITHUB_TOKEN_HINT` → exit 2 (fail with a reason).

**Changes** (via `/plan_update` engineer):
- `step_2.md`: bump smoke assertion 24→25; correct affected-test citations (drop 292; add 900/935/953-964) and patch `get_github_token` to a dummy token there.
- `step_3.md`: new 3b proactive guard on `--wait-for-pr` (print hint, return 2); hoisted `UNAVAILABLE → 2` (3d) before `--fix` block; added tests for `--fix`+no-token→2 and `--wait-for-pr`+no-token→hint+2.
- `summary.md`: updated detection sites, exit-code consistency, files/tests touched, and step descriptions.

**Status**: plan changed — commit pending, then re-review (loop).

## Round 2 — 2026-07-02

**Findings** (from `/plan_review` engineer, focused on round-1 revisions):
- All four round-1 revisions verified CORRECT against the real code (smoke count 24→25, the three `_collect_ci_status` test citations, hoisted `UNAVAILABLE → 2` above `--fix`, `--wait-for-pr` proactive guard). Guard ordering, import ordering, ready-to-merge gate, `format_for_llm` hint placement all confirmed sound.
- CRITICAL C1: Step 3's new guards (`--wait-for-pr` return-2 + `--ci-timeout` gate) break EXISTING tests in two sibling files the plan never named — `test_check_branch_status_pr_waiting.py` and `test_check_branch_status_ci_waiting.py` — which call `execute_check_branch_status` on the wait/PR paths without patching `get_github_token`. On a token-less runner they'd now return 2 / skip the wait and fail. Same class of miss as round-1 Step 2.
- DESIGN D1 (minor, non-blocking): `--fix N` now reaches the `UNAVAILABLE` path; behavior is already locked by tests asserting auto-fix not called. No change.

**Decisions**:
- C1 — accept (supervisor, straightforward test-repair scope, no user decision needed): name both sibling files in Step 3 and patch `get_github_token` to a dummy token in the affected wait/PR/ci-timeout tests.

**User decisions**: none this round.

**Changes** (via `/plan_update` engineer):
- `step_3.md`: WHERE + TESTS sections now name `test_check_branch_status_pr_waiting.py` (6 tests, incl. `test_wait_for_pr_no_remote_tracking`) and `test_check_branch_status_ci_waiting.py` (`test_execute_with_ci_timeout_waits_before_display`) as REQUIRED repair targets; patch `mcp_coder.cli.commands.check_branch_status.get_github_token` to a dummy token. `test_check_branch_status_auto_fixes.py` explicitly out of scope.
- `summary.md`: tests-touched list + Step 3 description updated.

**Status**: plan changed — commit pending, then re-review (loop).

## Round 3 — 2026-07-02

**Findings** (from `/plan_review` engineer, verifying round-2 fix + final consistency):
- Round-2 test-repair addition CONFIRMED correct and complete: all 6 `test_check_branch_status_pr_waiting.py` wait tests and `test_execute_with_ci_timeout_waits_before_display` genuinely hit the new guards and lack a `get_github_token` patch; no affected test missed; `test_check_branch_status_auto_fixes.py` correctly excluded; patch target path resolves.
- Full-plan consistency verified: `__all__` 24→25 correct; NO enum-exhaustiveness / parametrized `CIStatus` / `len(CIStatus)` tests exist (adding `UNAVAILABLE` breaks nothing); existing icon/recommendation tests for `NOT_CONFIGURED` untouched by the separate `UNAVAILABLE` branch; read-only/fix `execute` tests safe; detection stays proactive; summary.md matches step files.
- CRITICAL: none. DESIGN-QUESTION: none.
- IMPROVEMENT (cosmetic, non-blocking): Step 1's illustrative DATA line writes `CI=UNAVAILABLE (hint)` but the real `format_for_llm` appends the hint at the end of the full summary line; the prescribed test assertions (contains `CI=UNAVAILABLE`, contains hint) still pass. Doc-wording only.

**Decisions**:
- Cosmetic IMPROVEMENT — skip (supervisor): does not affect implementation or test outcomes; fixing it would trigger a needless extra review loop. Noted here instead.

**User decisions**: none this round.

**Changes**: none — zero plan files changed this round. Loop terminates.

**Status**: no changes needed — plan is clean.

## Final Status

- **Rounds run:** 3.
- **Commits produced:** 2 plan-update commits (`3315923`, `007c940`) + this log commit.
- **Round 1:** accepted 2 straightforward fixes (smoke-count assertion, corrected test citations); escalated 2 scope questions — user chose consistent exit 2 across `--fix` (hoist the check) and a clean-fail guard on `--wait-for-pr` (print hint + exit 2 instead of silent exit).
- **Round 2:** caught + fixed a test-repair gap (two sibling wait/ci-timeout test files needed `get_github_token` patched).
- **Round 3:** verified the round-2 fix and did a full-plan consistency sweep (enum-exhaustiveness, icon/recommendation, parametrized tests) — clean. Only a cosmetic doc-wording nit remains, intentionally left.
- **Verdict:** ✅ Plan is ready for approval. Core design was verified accurate against the real source throughout; each step is one commit and leaves pylint/pytest/mypy green; detection is proactive (`get_github_token()`), never string/type-matched.
