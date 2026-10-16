# Summary — PR-health: detect new review comments and threads (status-91)

Issue: #1214. Part of the PR-health epic (#1188). Mirrors the already-implemented
siblings #1212 (merge-conflict) and #1213 (CI) in
`src/mcp_coder/workflows/vscodeclaude/session_launch.py`.

## Goal

On the VSCodeClaude coordinator's existing `status-10:pr-created` poll, once the
conflict and CI checks both find nothing to act on, detect any unresolved review
thread, changes-requested review, or new top-level PR comment and escalate
directly to `status-91:pr-review-comments` — an interactive human session, no
auto-fix attempt.

## Architectural / design changes

- **New escalation label**: `status-91:pr-review-comments` (internal_id
  `pr_review_comments`) added to `labels.json`. A single `human_action` label —
  no `bot_pickup`/`bot_busy` pair, no crash-watchdog chain — because there is no
  unattended fix attempt to guard against double-dispatch for. Its `vscodeclaude`
  block wires it to a **new** slash command, `/pr_comment_triage` (not a reuse of
  `/check_branch_status`, since this one has reply/resolve work to do, not just
  inspection), with `requires_branch: true`.
- **Detection logic** lives in `session_launch.py`, next to its two siblings:
  - `_check_ci()` changes its return type from `None` to `bool` so the priority
    chain can short-circuit on it, matching `_check_merge_conflict()`.
  - A new `_check_review_comments()` follows the same shape: build a
    `PullRequestManager` via the existing `_build_pr_manager()` helper, resolve
    the PR number the same way `_check_merge_conflict()` already does
    (`branch_manager.get_branch_with_pr_fallback` →
    `pr_manager.find_pull_request_by_head`), then call
    `pr_manager.get_pr_feedback(pr_number)` directly for the raw `PRFeedback`
    struct. `collect_pr_feedback` is deliberately not used — it collapses the
    feedback into formatted text plus booleans, losing the per-comment
    `created_at` the watermark comparison needs.
  - **Trigger conditions**: any unresolved review thread, any changes-requested
    review, or a conversation comment newer than the watermark. Code-scanning
    alerts (`PRFeedback.alerts`) are excluded — handled elsewhere in the overall
    PR-health check.
  - **Watermark**: unresolved threads and changes-requested reviews use GitHub's
    own live state every poll (no watermark needed). Plain conversation comments
    have no such state, so a watermark — derived live from the issue's own
    label-change timeline, nothing persisted locally — prevents re-triggering on
    an already-handled comment. Algorithm, isolated into one pure helper,
    `_review_comments_watermark()`, so it is unit-testable against synthetic
    event lists with no GitHub mocking: find the *last* `LABELED` event for
    `status-91` in the issue's history, then the *next* `LABELED` event for
    `status-10` after it — that event's `created_at` is the watermark. If no
    `status-91` event exists anywhere in the history (first-ever arrival) —
    or, degenerate case, no `status-10` relabel follows the last `status-91`
    event — the helper returns `None`, which the caller treats as "no filter,
    any existing comment counts." Both edge cases collapse onto the same
    sentinel, which keeps the caller's branching to one `if`.
  - **Priority ordering**: `process_eligible_issues()`'s per-issue chain
    becomes a single short-circuiting expression —
    `_check_merge_conflict(...) or _check_ci(...) or _check_review_comments(...)`
    — preserving the exact conflict → CI → comments priority (a stale branch
    can itself cause spurious CI failures, so conflicts are resolved first)
    without nested `if`s.
  - The two label *names* needed for the watermark comparison (`status-91`'s
    and `status-10`'s actual GitHub label text, as opposed to their
    `internal_id`s) are resolved **once per poll**, before the per-issue loop,
    via the same `build_label_lookups`/`load_labels_config` utilities
    `label_transitions.py` already uses — not once per issue, which would
    reread and reparse `labels.json` for every `status-10` issue in the batch.
- **Reply mechanism** (used by the new skill, not by `session_launch.py`):
  inline reply (`github_review_comment_reply`) + thread resolution
  (`github_review_thread_resolve`) for unresolved-thread items, using the
  `comment_id`/`thread_id` `get_pr_feedback()` already surfaces; general PR
  comment (`gh pr comment`) for items with no such id (plain conversation
  comments, changes-requested reviews).
- **No shim changes** for `PRFeedback`/`get_pr_feedback` — called as a method on
  the already-imported `PullRequestManager`, so no new type import is needed.
  One small shim addition *is* needed: `EventData` (the return-item type of
  `get_issue_events()`) is not yet re-exported from
  `mcp_coder.mcp_workspace_github`, unlike `IssueEventType`, which already is.

## Folders / modules / files touched

| Path | Change |
|---|---|
| `src/mcp_coder/config/labels.json` | Add `status-91:pr-review-comments` workflow label |
| `tests/config/test_label_config.py` | Regression test asserting the new label's shape |
| `src/mcp_coder/mcp_workspace_github.py` | Re-export `EventData` alongside existing `IssueEventType` |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | `_check_ci()` → `bool`; new `_review_comments_watermark()` and `_check_review_comments()`; `process_eligible_issues()` chaining + one-time label-name resolution |
| `tests/workflows/vscodeclaude/test_session_launch_review_comments.py` | New file: unit tests for the watermark helper and `_check_review_comments()`, plus chaining/priority tests |
| `.claude/skills/pr_comment_triage/SKILL.md` | New slash command: triage new PR comments/threads — fix, reply, decline, resolve |

## Step order and commit boundaries

1. `labels.json` + its regression test (pure config, independently valid/invalid).
2. Shim `EventData` export + pure watermark helper + its unit tests (no GitHub
   mocking — synthetic `EventData` lists only).
3. `_check_review_comments()` + `_check_ci()` bool change + `process_eligible_issues()`
   chaining, with mocked-manager tests mirroring the existing conflict/CI test
   style.
4. New `/pr_comment_triage` skill file (no automated test — skill content has
   no test harness in this repo; verified by review only).

Each step lands as exactly one commit: tests (where applicable) + implementation
+ `run_pylint_check` / `run_pytest_check` / `run_mypy_check` all green.
