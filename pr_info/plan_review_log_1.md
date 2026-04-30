# Plan Review Log — Issue #844

**Issue:** icoder: show branch / issue / PR info area below status bar
**Branch:** 844-icoder-show-branch-issue-pr-info-area-below-status-bar
**Started:** 2026-04-30

## Round 1 — 2026-04-30

**Findings (from /plan_review):**
- Critical: Step 1's `get_pr_for_branch` mis-described `IssueBranchManager.get_branch_with_pr_fallback` — it returns a branch name, not a PR number.
- Critical: Step 1 unspecified how to derive GitHub `repo_url`/owner/name from `project_dir`.
- Critical: Tach.toml + `.importlinter` wiring loose — new `mcp_coder.services` module entry needed `depends_on` direction.
- Improvement: Step 1 dirty-detection used a raw subprocess instead of the existing `is_working_directory_clean` shim helper.
- Improvement: Step 1 hardcoded the cache file path instead of using `_get_cache_file_path(repo_id)`.
- Improvement: Step 2 widget API took two extra `set` args; KISS suggests one immutable view.
- Improvement: Step 4 PR-fetch race window when toggle flips during in-flight fetch.
- Improvement: Step 4 `compose()` placement guidance ambiguous (sibling vs. child of status-bar).
- Improvement: Step 2 button-press test referenced non-existent `app.message_queue`.
- Improvement: Step 1 status-label tests missing parameterized multi-`status-` case.
- Improvement: Step 5 (docs-only) too small — merge into Step 4 per `planning_principles.md`.

**Decisions:**
- Accepted (autonomous): all improvement items above + critical wiring item.
- Escalated to user: PR-number lookup mechanism (Question A); repo-identity helper (Question B).

**User decisions:**
- Q-A: Two-step PR lookup — `get_branch_with_pr_fallback` → branch, then `PullRequestManager.find_pull_request_by_head(branch)` → `.number`.
- Q-B: Reuse existing helper. Audit confirmed `get_repository_identifier(project_dir)` already returns a fully populated `RepoIdentifier`. No gap.

**Gap audit (user-requested):** No gaps. All 8 capabilities (git-repo detection, branch name, dirty status, issue # extraction, cache lookup, repo identity, PR lookup, status color) are reachable via existing public helpers in `mcp_workspace_git`, `mcp_workspace_github`, and `config.label_config`.

**Changes (via /plan_update):**
- `pr_info/steps/step_1.md` — rewrote PR lookup as two-step; replaced manual repo-URL parsing with `get_repository_identifier`; replaced subprocess dirty-detection with `is_working_directory_clean`; cache path via `_get_cache_file_path`; deterministic tach + import-linter wiring; status-color builds inline at widget mount; added parameterized status-label test.
- `pr_info/steps/step_2.md` — introduced `BranchInfoView` frozen dataclass for a single-arg `update_state` API; replaced `app.message_queue` test with Textual `Pilot` pattern; status-color mapping now built inline at mount.
- `pr_info/steps/step_4.md` — added monotonic `pr_fetch_generation` race protection (incremented on start + on toggle-off); race test added; explicit `compose()` snippet shows widget yielded as sibling of `status-bar`; doc work folded in as a "Documentation" sub-section.
- `pr_info/steps/step_5.md` — deleted (folded into Step 4).
- `pr_info/steps/summary.md` — implementation order updated to 4 steps.
- `pr_info/steps/Decisions.md` — created (per /plan_update skill).

**Status:** Pending commit (to be handled by commit agent).

## Round 2 — 2026-04-30

**Findings (from /plan_review):**
- Critical: Step 3 still referenced `get_pr_for_branch` (renamed to `get_pr_for_issue` in round 1) in three places — would break the import.
- Improvement: Step 3 contained two contradictory exception-policy phrasings ("catches internally" vs. "lets propagate"); had to be reconciled.
- Improvement: Step 4 ALGORITHM block called `apply_pr` while HOW prose specified `_apply_branch_state` — naming drift.
- Improvement: `summary.md` listed `pr_fetch_generation` on the adapter, but Step 3 didn't mention it (added in Step 4) — reader confusion.
- Improvement: Step 1 missing test for cache-miss path (`get_all_cached_issues` returns empty).
- Improvement: Step 4 missing 2s-tick variant of the toggle-off mid-fetch race test.
- Improvement (Boy Scout): Step 1 imported underscore-prefixed `_get_cache_file_path` / `_load_cache_file` from the shim — violates public-API convention.

**Decisions:**
- Accepted (autonomous): all critical + improvement items above.
- Escalated to user: should the underscore-prefix cache helpers be promoted to public re-exports as a Boy Scout fix? (One question — single-decision impact.)

**User decisions:**
- Promote `_get_cache_file_path` / `_load_cache_file` to public re-exports (`get_cache_file_path` / `load_cache_file`) in `mcp_workspace_github.py`. Existing call sites updated as part of Step 1.

**Changes (via /plan_update):**
- `pr_info/steps/step_3.md` — renamed function references to `get_pr_for_issue`; resolved exception policy to "propagates"; added forward-pointer for `pr_fetch_generation` (added in Step 4).
- `pr_info/steps/step_4.md` — replaced `apply_pr` with `_apply_branch_state` in ALGORITHM; added test #10 (`test_pr_fetch_race_via_2s_tick_dropped_on_toggle_off`).
- `pr_info/steps/step_1.md` — added test 4b (`test_cache_miss_returns_branchinfo_with_none_issue_fields`); promoted cache helpers to public names; updated WHERE/HOW/ALGORITHM to use `get_cache_file_path` / `load_cache_file`; logged existing call sites for the rename.
- `pr_info/steps/summary.md` — updated cache-helper names to public versions.
- `pr_info/steps/Decisions.md` — appended "Round 2" section with the six round-2 decisions.

**Status:** Pending commit (to be handled by commit agent).

## Round 3 — 2026-04-30

**Findings (from /plan_review):**
- Critical: Step 4's `compose()` snippet referenced an undefined local `project_dir` — un-runnable as written.
- Improvement: Step 4's HOW described `_last_branch_info` but its init block didn't declare it.
- Improvement: Round-2 Boy Scout rename was incomplete — `_save_cache_file` and `_log_stale_cache_entries` still underscore-prefixed in the same shim.
- Improvement: Step 4 test #6 description was slightly stale after test #10 was added (overlapping coverage).

**Decisions:**
- All four items handled autonomously (no user escalation). The Boy Scout extension follows the round-2 user policy by simple analogy.

**User decisions:** None (no items escalated).

**Changes (via /plan_update):**
- `pr_info/steps/step_4.md` — `__init__` now stores `self._project_dir`; `compose()` and `BranchInfoService` both consume it; snippet is copy-pasteable. Added `self._last_branch_info: BranchInfo | None = None` to init. Test #6 renamed and tightened (refresh-PR-button path explicit; generation-token assertion specific).
- `pr_info/steps/step_1.md` — WHERE block extends Boy Scout rename to `save_cache_file` and `log_stale_cache_entries`; concrete call sites (in `tests/cli/commands/coordinator/test_core.py`) listed; HOW + summary.md updated for consistency.
- `pr_info/steps/summary.md` — cache-helper public names propagated.
- `pr_info/steps/Decisions.md` — appended Round 3 section (R3-#1 through R3-#4).

**Status:** Pending commit (to be handled by commit agent).

