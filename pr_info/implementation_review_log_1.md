# Implementation Review Log — Issue #953

**Branch:** 953-vscodeclaude-session-detection-improvements
**Started:** 2026-05-12
**Supervisor:** Claude (Opus 4.7)
**Issue:** #953 — vscodeclaude: session detection improvements

This log tracks the supervisor-led implementation review of the 8-step
implementation for issue #953 (vscodeclaude session detection improvements).
Each round corresponds to one full `/implementation_review` cycle by an
engineer subagent, with findings, supervisor triage decisions, and any
follow-up changes documented below.


## Round 1 — 2026-05-12

**Findings**:
- F1: `tests/workflows/vscodeclaude/test_cleanup.py::TestCompositionScenarios::test_false_negative_reconciliation` does not monkeypatch `get_sessions_file_path`, so `cleanup_stale_sessions` → `load_sessions()` reads the developer's real `vscodeclaude_sessions.json`. Reproduced one failing run with a leaked `safe_delete_calls` entry.
- F2: `src/mcp_coder/workflows/vscodeclaude/sessions.py` grew from 651 → 730 lines, deeper into the existing >600-line tracking band.
- F3: `is_session_active` at `sessions.py:627` uses subscript on `session["vscode_pid_create_time"]`, relying on the Option-B load-time backfill / `build_session` initialization invariant. No docstring at this read site spells the invariant out.
- F4: `helpers.py:build_session` initializes `vscode_pid_create_time` to `None` instead of taking it as a parameter (plan said "take and store"). Documented override in `pr_info/steps/summary.md`.
- F5: Per-repo at-capacity log downgraded to DEBUG (not removed). Matches "drop or downgrade" wording in the plan; orchestrator-level OUTPUT log in `commands.py:631-649` is the new authoritative emission.

**Quality gates** (engineer-run): pylint PASS, mypy PASS, ruff PASS, vulture PASS, lint-imports PASS (23 contracts kept). Scoped pytest (vscodeclaude + coordinator, fast unit): 639 passed, 2 skipped — clean when test isolation is honored; the one transient failure observed was F1.

**Decisions**:
- F1 — **Accept**. Real isolation defect, trivial fix, clear precedent in the Scenario-A sibling test.
- F2 — **Skip**. Pre-existing line-count violation (file was already >600 lines at the merge base). SE principles: pre-existing issues are out of scope.
- F3 — **Accept**. Borderline cosmetic, but the invariant is non-obvious at the read site and a one-line docstring note pays off for future contributors. Defaulting to better code quality per supervisor guidance.
- F4 — **Skip**. Intentional override approved during plan review, explicitly documented in `summary.md` under the Option-B "override notice".
- F5 — **Skip**. Matches plan, no action required.

Out of scope:
- Pre-existing pytest collection error in `tests/checks/test_branch_status.py` (unrelated CLI argument mismatch surfaced by repo-wide collection; not introduced by #953).

**Changes**: pending engineer follow-up:
1. Add `monkeypatch.setattr("mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path", lambda: sessions_file)` to `test_false_negative_reconciliation`, matching the Scenario-A test's pattern (currently `tests/workflows/vscodeclaude/test_cleanup.py:2587`).
2. Append a short note to the `is_session_active` docstring (or an inline comment immediately above the subscript at `sessions.py:627`) clarifying that the `vscode_pid_create_time` key is guaranteed by `load_sessions`/`build_session` so subscript is safe.

**Status**: committed as `998c471`. Test isolation fix verified deterministic across reruns; docstring note added. Working tree clean.


## Round 2 — 2026-05-12

**Findings**:
- F6 (pre-existing/borderline): comment at `src/mcp_coder/workflows/vscodeclaude/cleanup.py:82-85` says "If both the folder and workspace file are gone, the VSCode process is a zombie ..." — Step 3 tightened `session_has_artifacts` to folder-only, so the "and workspace file" qualifier is now superfluous wording. The engineer who raised it explicitly noted it is NOT a defect and NOT a Round 3 blocker.

**Quality gates** (engineer-run): pylint PASS, mypy PASS, ruff PASS, lint-imports 23/23 contracts kept. Full fast-unit pytest sweep over the changed packages: 493 vscodeclaude + 146 coordinator + balance = 3822 passed, 2 skipped, 0 failed. `test_false_negative_reconciliation` confirmed deterministic across reruns (Round 1 fix held). Vulture's one 60% hit on `vscode_pid_create_time` is the expected TypedDict-field false positive.

**Plan conformance**: all 8 steps match the plan exactly. Cross-references verified against `pr_info/steps/step_1.md` … `step_8.md` and the issue #953 spec.

**Decisions**:
- F6 — **Skip**. The comment still captures the zombie scenario faithfully; only the "and workspace file" qualifier is slightly imprecise post-Step 3. Behavior is correct, the surrounding code is readable. Per SE principles, do not change working code for cosmetic reasons; a one-line comment tweak does not justify another commit + review loop iteration.

**Changes**: none — Round 2 produced zero code changes.

**Status**: clean. Loop exit condition met (one full round with zero code changes). Proceeding to vulture + lint-imports supervisor-level checks.


## Supervisor-level Checks — 2026-05-12

- **vulture**: initial run flagged one 60%-confidence finding on the new `vscode_pid_create_time` TypedDict field. Resolved by adding `_.vscode_pid_create_time` to `vulture_whitelist.py` directly after the sibling `_.started_at` entry (commit `52e7a62`, `chore(vulture): whitelist vscode_pid_create_time TypedDict field`). Re-run: clean.
- **lint-imports**: PASS on both runs — 23/23 contracts kept, no architectural violations.

## Final Status

- **Rounds**: 2 (Round 1 produced two follow-up fixes; Round 2 produced zero code changes — exit condition met).
- **Commits produced by this review**:
  - `998c471` — `test(vscodeclaude): isolate scenario B from real sessions.json + docstring`
  - `52e7a62` — `chore(vulture): whitelist vscode_pid_create_time TypedDict field`
- **Quality gates (final state)**: pylint PASS, mypy PASS, ruff PASS, vulture PASS (clean), lint-imports PASS (23 contracts kept), fast-unit pytest PASS for the changed packages with `test_false_negative_reconciliation` now deterministic.
- **Plan conformance**: all 8 steps verified to match `pr_info/steps/summary.md` and the per-step plans, with the one approved override (`build_session` always initializes `vscode_pid_create_time=None` rather than taking it as a parameter — documented in summary.md).
- **Open items**: none. One pre-existing comment imprecision in `cleanup.py:82-85` was reviewed and explicitly skipped as a non-defect.
- **Outcome**: implementation is clean and ready for the PR-review stage.
