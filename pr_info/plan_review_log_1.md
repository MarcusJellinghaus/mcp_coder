# Plan Review Log — Run 1

Issue: #1085 — `mcp-coder rebase`: execute git in Python, LLM only for conflict resolution; add CLI progress output
Branch: 1085-mcp-coder-rebase-execute-git-in-python-llm-only-for-conflict-resolution-add-cli-progress-output
Date: 2026-07-26
Reviewer: plan_review_supervisor

Note: branch is behind origin/main by one docs-only commit (5357e07, `.claude/CLAUDE.md`); review proceeds since it cannot affect the plan.

## Round 1 — 2026-07-26

**Findings** (engineer review, verified against code):
1. CRITICAL — step_2/summary: pytest `error_info` is set for ordinary test failures too (`mcp-tools-py` runners.py:336-340, 554-571), not only infra failures. As written: red baseline → exit 2, and pytest regressions bypass the fix loop. Correct predicate: `success is not True or test_results is None` → `CheckRunError`.
2. CRITICAL — step_3: `_binary_conflict` (bare `git diff --numstat` at conflict stop) has no planned test; mechanism unverified and may misclassify every text conflict as binary. Add positive+negative `git_integration` tests; fall back to stage-blob comparison (`git ls-files -u` + blob-level numstat) if ambiguous.
3. IMPROVEMENT — step_1/2: annotating with library result types directly would break the `mcp_checker_isolation` import-linter contract; re-export `PylintResult` etc. from the `mcp_coder.mcp_tools_py` shim instead.
4. IMPROVEMENT — step_2/summary: add `xpassed` to non-failure pytest outcomes (same rationale as skipped/xfailed; avoids unfixable phantom regressions).
5. IMPROVEMENT — step_6: `git rebase --continue` refuses on empty commit (conflict resolved to base's version) → currently a generic abort. Design question → user.
6. COSMETIC — steps 3-5: stage `:1:` mislabeled "base"; rename to "common ancestor (merge base)" to avoid clashing with "base branch".
7. COSMETIC — step_1: document both return shapes of `run_pytest_check` (success dict incl. `summary_text`; crash dict `{success: False, error}`).

**Decisions**:
- Accept 1 (factual correction against library code; issue's intent — exit 2 when a check cannot run — preserved, only the detection predicate changes).
- Accept 2, 3, 4, 6, 7 (straightforward correctness/test/clarity fixes).
- Also accept reviewer's suggestion: add an OUTPUT-level warning line "N pre-existing failures in baseline" to step 6 logging spec (simple, matches issue's logging requirement).
- Escalate 5 (empty-commit handling: auto `--skip` vs documented abort) to user.

**User decisions**: Empty-commit handling — user chose option A: Python detects the nothing-to-commit state after a failed `git rebase --continue` and runs `git rebase --skip` (fully automated; the commit's content already exists on base). Other non-conflict failures still abort.

**Changes** (applied via /plan_update):
- step_1.md: shim re-exports `PylintResult`; both `run_pytest_check` return shapes documented.
- step_2.md: infra predicate now `success is not True or test_results is None` (explicit "do NOT key off error_info"); `xpassed` non-failure; new TDD case (success+failures+error_info → keys, not CheckRunError); annotations import from shim only.
- step_3.md: two mandatory `git_integration` tests for `_binary_conflict` (text → None, binary → path); documented numstat fallback (`git ls-files -u` + blob-level numstat); stage `:1:` relabeled.
- step_4.md / step_5.md: stage `:1:` relabeled "common ancestor (merge base)" in prompt specs.
- step_6.md: empty-commit auto-skip in conflict-loop pseudocode (+ TDD case 5a); OUTPUT baseline warning line.
- summary.md: aligned (infra detection wording, xpassed, auto-skip).
- Decisions.md: new — logs the 8 decisions incl. user's option A.

**Status**: committed
