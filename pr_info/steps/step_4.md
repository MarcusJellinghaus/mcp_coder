# Step 4 — `/pr_comment_triage` skill

See `pr_info/steps/summary.md` for full context. This step adds the
dispatch target `status-91`'s `vscodeclaude.commands` (set in step 1) points
to. No Python changes; no dispatch code is needed — the existing VSCodeClaude
session-launch mechanism already runs whatever `commands` a `human_action`
label declares.

## LLM prompt

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_4.md` exactly as written. There is no automated test for
> skill content in this repo (confirmed: no test enumerates real
> `.claude/skills/*/SKILL.md` files) — TDD does not apply here. Produce
> exactly one commit for this step.

## WHERE

- `.claude/skills/pr_comment_triage/SKILL.md` (new file).

## WHAT

A skill frontmatter + body, following the shape of
`.claude/skills/check_branch_status/SKILL.md` and `.claude/skills/rebase/SKILL.md`.

## HOW

Create the file with this content (the issue's draft, with `allowed-tools`
corrected to add the `git commit`/`push` permissions the "Fix" path needs —
missing from the original draft):

```markdown
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
  - mcp__mcp-tools-py__run_format_code
  - mcp__mcp-tools-py__run_pylint_check
  - mcp__mcp-tools-py__run_pytest_check
  - mcp__mcp-tools-py__run_mypy_check
  - "Bash(git add *)"
  - "Bash(git commit *)"
  - "Bash(git push *)"
  - "Bash(gh pr comment *)"
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
    comment via `gh pr comment`.
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
```

## ALGORITHM

N/A — this is a prompt/instruction file, not executable logic.

## DATA

N/A.

## Quality checks

Run `mcp__mcp-tools-py__run_pytest_check`, `mcp__mcp-tools-py__run_pylint_check`,
`mcp__mcp-tools-py__run_mypy_check` for parity with every other step (expected
to be unaffected, since no `.py` file changes) before committing.
