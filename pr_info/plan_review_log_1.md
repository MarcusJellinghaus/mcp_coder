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

