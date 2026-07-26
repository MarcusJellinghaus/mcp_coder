# Decisions — plan review round 1 (Issue #1085)

Source: plan review findings, all accepted at triage; empty-commit handling decided
by the user.

1. **Pytest infrastructure predicate** (review finding, accepted): a check "fails to
   run" when `success` is not `True` or `test_results` is missing — NOT when
   `error_info` is set (the library sets `error_info` for any non-zero pytest exit,
   including ordinary failures and collection errors). Failure keys come from
   `report.tests` + non-passed collectors. The decision's intent (baseline must be
   runnable → exit 2) is unchanged; only the detection mechanism was corrected.
2. **Binary-conflict detection must be test-verified** (review finding, accepted):
   Step 3 gains mandatory `git_integration` tests for `_binary_conflict` (text
   conflict → `None`; binary conflict → path). If bare `git diff --numstat` proves
   ambiguous at a conflict stop, fall back to `git ls-files -u` + blob-level
   `git diff --numstat <ours> <theirs>`.
3. **Result types import via the shim only** (review finding, accepted): the shim
   `mcp_coder.mcp_tools_py` re-exports `PylintResult` (and other needed result
   types); `workflows/rebase.py` never imports `mcp_tools_py` directly
   (import-linter `mcp_checker_isolation` contract).
4. **`xpassed` is not a failure key** (review finding, accepted): excluded alongside
   `passed`/`skipped`/`xfailed` — a non-strict xpass is not a regression the LLM
   can fix.
5. **Empty commit during the conflict loop → auto-skip** (user decision, option A):
   when `git rebase --continue` fails because the resolved commit became empty
   (mid-rebase, no conflicted files, `git diff --cached --quiet` clean), Python runs
   `git rebase --skip` and logs at OUTPUT that the commit was skipped as redundant.
   Other non-conflict failures still abort.
6. **Stage `:1:` terminology** (review finding, accepted): labeled "common ancestor
   (merge base)" everywhere — never bare "base", which collides with "base branch"
   (`:2:`).
7. **`run_pytest_check` return shapes documented** (review finding, accepted): the
   success dict (incl. `summary_text`, `error_info` semantics) and the crash dict
   `{"success": False, "error": ...}` are both documented in Step 1.
8. **Red-baseline visibility** (accepted at triage): Step 6 logs an OUTPUT-level
   warning when the baseline contains pre-existing failures ("N pre-existing
   failure(s) in baseline — these will not block the rebase").

## Round 2 (all accepted at triage)

9. **Generic exception after a completed rebase → reset** (review finding, accepted):
   in Step 6's `except Exception` handler, when NOT mid-rebase (LLM/unexpected
   failure during the regression-fix phase), Python runs `_reset_hard(pre_sha)`
   before exiting 1; the `finally` net still owns the mid-rebase case. Same
   invariant as the CheckRunError-at-verification and push-rejection paths:
   never leave a rebased-but-unpushed or dirty state behind. TDD case added.
10. **SKILL.md drift test survives** (review finding, accepted): Step 4 re-targets
    `test_prompt_conflict_strategy_matches_skill` at the "Rebase Conflict
    Resolution" section, restricted to the code/test/config strategy rows
    (`pr_info/` and lockfile rows intentionally omitted — Python handles those);
    Step 6 must not delete it.
11. **Stage `:1:` label leftover in summary fixed** (review finding, accepted):
    the "Design change" section now reads "common-ancestor (merge base)/ours/
    theirs", per decision 6 (never bare "base").
