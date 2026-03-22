# Implementation Review Log — #264

Branch: `264-coordinator-detect-unlinked-branches-by-issue-number-pattern`

## Round 1 — 2026-03-22
**Findings**:
- #1 Prefix pass returns extra refs for issue numbers that are prefixes of others (not a bug)
- #2 `list()` materializes all branches before truncating to 500 — lazy iteration suggested
- #3 Stale docstring on `get_branch_with_pr_fallback` — says "two-step" but is now 4-step
- #4 Bracket access vs `.get()` defensiveness regression in `_extract_prs_by_states`
- #5 Full-scan path not exercised for false-positive test case
- #6 Steps 2-3 (caller migration) not yet implemented
- #7 f-string in logging (consistent with project style)
- #8 Duplicated `mock_manager` fixture across test classes
- #9 Inconsistent test helper placement (module-level vs class-level)
- #10 `cast()` noise on values already typed as `str`

**Decisions**:
- #1 Skip — observation, code is correct
- #2 Skip — YAGNI, speculative optimization
- #3 Accept — docstring actively contradicts current behavior
- #4 Skip — speculative, guard is correct
- #5 Skip — prefix-pass regex rejection is tested, full-scan tested elsewhere
- #6 Skip — expected per plan, tracked in TASK_TRACKER.md
- #7 Skip — consistent with existing project style
- #8 Skip — cosmetic, don't change working code
- #9 Skip — cosmetic
- #10 Skip — correct for type safety given `Any` types

**Changes**: Updated `get_branch_with_pr_fallback()` docstring to accurately describe the 4-step resolution strategy.
**Status**: Committed (8218f4e)

## Round 2 — 2026-03-22
**Findings**:
- #1 Redundant `repo_owner`/`repo_name` parameters create inconsistency risk
- #2 Closed-PR fallback returns first surviving branch without ambiguity check, contradicting docstring
- #3 No test for multiple matches in full-scan pass of `_search_branches_by_pattern`

**Decisions**:
- #1 Skip — speculative, single caller passes matching values
- #2 Accept — docstring updated in Round 1 still claims "at each step, multiple matches → None" but closed-PR step intentionally returns most recent
- #3 Skip — same logic as prefix pass, already tested there

**Changes**: Refined docstring to clarify that steps 1/2/4 treat multiple matches as ambiguous, while step 3 returns the most recent closed PR.
**Status**: Committing
