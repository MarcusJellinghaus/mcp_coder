# Summary — #1240: status-91 re-triggers on triaged reviews and automated ❌ notes

## Problem

`_check_review_comments()` (`src/mcp_coder/workflows/vscodeclaude/checks.py`) escalates
`status-10:pr-created` → `status-91:pr-review-comments` on PR feedback. Two defects:

1. **Changes-requested loop** — any standing `CHANGES_REQUESTED` review escalates on every
   poll, with no watermark. The triage session cannot dismiss it, so the issue bounces between
   `status-10` and `status-91` until the reviewer re-reviews.
2. **Automated ❌ notes** — mcp-coder's own failure/handoff notes (first line contains ❌)
   would count as human feedback if one landed on the PR.

## Design changes

Only the escalation trigger is narrowed; `/check_branch_status` and mcp-workspace are unchanged.

| Feedback kind | Before | After |
|---|---|---|
| Unresolved review threads | live state, always count | unchanged |
| Changes-requested reviews | live state, always count | count if `submitted_at is None`, no watermark, or `submitted_at > watermark` |
| Conversation comments | watermark on `created_at` | skipped if the first line of `body` contains ❌; otherwise same watermark rule |

- **One filtering step.** Inside `_check_review_comments()`: pick the items that count (drop
  ❌-marked comments), collect their timestamps, compare them against the watermark once.
  #1257 will add its trust condition to the same comprehension.
- **Events fetch.** `get_issue_events` is called at most once per issue, and only when there
  are no unresolved threads and at least one review or unmarked comment.
- **Shared ❌ rule.** New `is_marked(body, marker="❌")` in
  `workflows/vscodeclaude/helpers.py` (already imported by both `checks.py` and
  `workspace.py`; no cycle). `_find_marked_comment` in `workspace.py` is refactored to use it,
  so the first-line rule exists once in mcp-coder. mcp-workspace keeps its own copy in
  `formatters.find_latest_marked_comment` on purpose.
- **Shim.** `ChangesRequestedData` and `ConversationCommentData` (from
  `mcp_workspace.github_operations.pr_types`) are re-exported through
  `mcp_coder.mcp_workspace_github` so tests can build typed fixtures without importing
  `mcp_workspace` directly.
- **Watermark** stays derived from the issue's label timeline (`_review_comments_watermark`,
  unchanged); nothing is stored locally.
- **No** author/self filter, `[bot]` rule, ignore list or auto-dismiss of reviews.
- **Triage skill.** A changes-requested review that has been replied to or fixed no longer
  blocks `set-status status-10:pr-created`; `/check_branch_status` is re-run right before
  `set-status`. Replies are posted before the relabel, so the new watermark excludes them.

## Files

| File | Change |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/helpers.py` | add `is_marked()` |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | `_find_marked_comment` uses `is_marked()` |
| `tests/workflows/vscodeclaude/test_helpers.py` | `is_marked()` tests |
| `src/mcp_coder/mcp_workspace_github.py` | re-export `ChangesRequestedData`, `ConversationCommentData` |
| `src/mcp_coder/workflows/vscodeclaude/checks.py` | new filtering in `_check_review_comments()` |
| `tests/workflows/vscodeclaude/test_checks_review_comments.py` | typed fixtures, new cases |
| `.claude/skills/pr_comment_triage/SKILL.md` | trigger description, "When done" gate |
| `docs/processes-prompts/development-process.md` | section 10 trigger + triage paragraphs |
| `docs/coordinator-vscodeclaude.md` | trigger line (~114) |
| `docs/getting-started/label-setup.md` | `status-91` row (~304) |

No files or folders are created besides `pr_info/steps/`.

## Steps

1. `is_marked()` helper + `_find_marked_comment` refactor.
2. Shim re-export + filtering in `_check_review_comments()` + tests.
3. Triage skill + docs.
