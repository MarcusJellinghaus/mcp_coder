# Plan Review Log — Issue #701

Cache: incremental refresh permanently misses issues on silent API failure

## Round 1 — 2026-04-06
**Findings**:
- (Critical) Direct callers of `list_issues()` would crash after removing the decorator — 4 call sites unprotected
- (Critical) `_fetch_and_merge_issues` clears `cache_data["issues"] = {}` on full refresh before calling `list_issues()` — if API raises, try/except returns empty list (data loss)
- (Improvement) Step 3 test description has confusing parenthetical about `state="open"` vs `state="all"`
- (Improvement) Step 2 should note dependency on step 1
- (Improvement) Fix 3 (redundant status cache call) not covered — noted as deferrable
- 8 positive confirmations (accuracy of code snippets, backward compatibility, step boundaries, etc.)

**Decisions**:
- User chose two-function design: `list_issues()` (safe, keeps decorator) + `_list_issues_no_error_handling()` (raises, used by cache). Eliminates all caller-update scope.
- Accept snapshot-restore fix for cache mutation
- Accept minor clarifications (test description, step dependency)
- Skip Fix 3 (redundant status call) — deferrable, not a correctness issue

**User decisions**: Two-function split design instead of removing the decorator

**Changes**: Rewrote all 4 plan files (summary, steps 1-3) with new two-function design, snapshot restore in step 2, clarified test descriptions

**Status**: Changes applied

## Round 2 — 2026-04-06
**Findings**:
- (Critical) `mock_cache_issue_manager` fixture mocks `list_issues` — will break after step 2 switches cache to call `_list_issues_no_error_handling()`. Must update fixture.
- (Improvement) Snapshot placement should clarify: after `additional_dict` merge, before fetch
- (Improvement) Step 3 must update the call inside step 2's try/except to unpack tuple return

**Decisions**:
- Accept all three — straightforward fixes, no design questions

**User decisions**: None needed

**Changes**: Updated step_2.md (fixture update, snapshot precision) and step_3.md (coordination note)

**Status**: Changes applied

## Round 3 — 2026-04-06
**Findings**: None — plan is internally consistent, function names match across files, all prior issues resolved.

**Changes**: None

**Status**: No changes needed

## Final Status

- **Rounds**: 3 (2 with changes, 1 clean)
- **Plan status**: Ready for implementation
- **Open items**: Fix 3 (redundant status cache call) deferred — not a correctness issue
