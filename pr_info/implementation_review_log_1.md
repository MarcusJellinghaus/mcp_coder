# Implementation Review Log — Issue #189

**Issue:** Implement workflow failure handling and error UX improvements
**Branch:** 189-implement-workflow-failure-handling-and-error-ux-improvements
**Reviewer:** Automated supervisor

## Round 1 — 2026-03-27
**Findings:**
- (Critical) CI check (Step 5.6) nested inside `if not finalisation_success:` — only runs when finalisation fails, skipping CI on the happy path
- (Critical) `tasks_total` never populated in `WorkflowFailure` — progress line ("2/5 tasks completed") never shown due to `tasks_total > 0` guard
- (Accept) `_get_diff_stat()` uses `repo.git.diff("--stat")` which only captures unstaged changes — misses staged-but-uncommitted
- (Skip) Duplicate `IssueManager` instantiation in `_handle_workflow_failure` — defensive pattern, safe as-is
- (Skip) Importing private `_safe_repo_context` — pre-existing, accepted in plan review

**Decisions:**
- Accept: Fix 1 (CI check gating) — regression, CI never checked on happy path
- Accept: Fix 2 (tasks_total) — spec requires progress in failure comment
- Accept: Fix 3 (diff stat scope) — "uncommitted changes" should include staged
- Skip: Duplicate IssueManager — minor optimization, not a correctness issue
- Skip: Private import — out of scope, pre-existing pattern

**Changes:**
- Dedented CI check block to run regardless of finalisation success
- Added `total_tasks` computation via `get_step_progress()` before task loop; passed to all relevant `WorkflowFailure` calls
- Changed `_get_diff_stat` to use `repo.git.diff("HEAD", "--stat")`
- Updated corresponding test assertion for diff stat

**Status:** Pending commit
