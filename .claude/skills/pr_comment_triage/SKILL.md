---
description: Triage new PR comments and review feedback, decide fix vs reply vs decline
allowed-tools:
  - mcp__mcp-workspace__check_branch_status
  - mcp__mcp-workspace__github_pr_view
  - mcp__mcp-workspace__git
  - mcp__mcp-workspace__read_file
  - mcp__mcp-workspace__edit_file
  - mcp__mcp-workspace__save_file
  - mcp__mcp-workspace__github_review_comment_reply
  - mcp__mcp-workspace__github_review_thread_resolve
  - mcp__mcp-workspace__github_issue_comment
  - mcp__mcp-tools-py__run_format_code
  - mcp__mcp-tools-py__run_pylint_check
  - mcp__mcp-tools-py__run_pytest_check
  - mcp__mcp-tools-py__run_mypy_check
  - "Bash(git add *)"
  - "Bash(git commit *)"
  - "Bash(git push *)"
  - "Bash(mcp-coder gh-tool set-status *)"
---

# PR Comment Triage

Call `/check_branch_status` first — it reports unresolved review threads
(with `comment_id`/`thread_id`), changes-requested reviews, and new PR
comments.

## For each item

- **Fix**: change code, run quality checks
  (`mcp__mcp-tools-py__run_format_code`, then pylint/pytest/mypy), commit and
  push, re-run `/check_branch_status`.
- **Reply**: no code change — explain why.
  - Unresolved-thread item (has `comment_id`): inline reply via
    `mcp__mcp-workspace__github_review_comment_reply(pr_number, comment_id, body)`.
  - Plain conversation comment or changes-requested review (no id): general PR
    comment via `mcp__mcp-workspace__github_issue_comment(pr_number, body)`
    (GitHub's comment endpoint is shared between issues and PRs).
- **Decline**: out of scope — say why, same reply path as above.
- **Resolve**: once an unresolved-thread item has been addressed (fixed or
  replied to), resolve it via
  `mcp__mcp-workspace__github_review_thread_resolve(pr_number, thread_id)` so
  it doesn't re-trigger `status-91` next poll. If this raises "already
  resolved", treat the thread as already handled and continue — not a
  failure.

## When done

CI green, no rebase needed, no unresolved new items:

    mcp-coder gh-tool set-status status-10:pr-created
