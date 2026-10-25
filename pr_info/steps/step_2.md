# Step 2 — Per-process docs: code review, PR creation, PR merge

## LLM prompt

> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_2.md`).
> Create the three docs listed under WHERE in `docs/processes-prompts/processes/`. Use the fixed layout and rules from the summary. Use the same structure as the step 1 docs.
> Take content from the current `docs/processes-prompts/development-process.md`. Do not modify it.
> Verify target labels against each skill's `SKILL.md`.
> Links may only point to existing files: the step 1 docs are fine; `pr-follow-up.md`, `automated-review.md` and `failure-handling.md` do not exist yet.
> Run the file-size check, then format, then commit as one commit.

## WHERE

```
docs/processes-prompts/processes/code-review.md   (new)
docs/processes-prompts/processes/pr-creation.md   (new)
docs/processes-prompts/processes/pr-merge.md      (new)
```

## WHAT — content per doc

Line numbers refer to the current `development-process.md`.

### `code-review.md`

- **Labels:** `status-07:code-review` (human_action), with these exits:
  - → `status-08:ready-pr` (approve)
  - → `status-05:plan-ready` (rework: new tasks, then re-implement)
  - minor fixes stay on 07
  - fundamental problems → `status-04:plan-review` or `status-01:created` via `mcp-coder gh-tool set-status`
- **Actor:** human or supervisor skill.
  - vscodeclaude auto-launches `/implementation_review_supervisor`.
  - The supervisor ends at "ready for approval". The transition is a separate command.
- **Slash commands:**
  - `/implementation_review_supervisor`, `/implementation_review`, `/discuss`, `/implementation_finalise`, `/implementation_new_tasks`, `/commit_push`.
  - `/implementation_approve` (→ 08, only when `/check_branch_status` reports `Ready to merge`).
  - `/implementation_needs_rework` (→ 05: next step is implementation, not plan review).
  - `/issue_approve` (07 → 08).
  - Rework chain: `/implementation_new_tasks` → `/commit_push` → `/implementation_needs_rework`.
- **Failure exits:** "None — human stage."
- **Prompts:**
  - The two-review-modes text (lines 798–804) becomes short rows in the Slash commands table.
  - Move verbatim into "Additional prompt details":
    - lines 806–840 "Code Review Prompt" — the `Code Review Request` block, including its quoted `Slash Command:` header (the issue says to move it unchanged);
    - lines 842–857 "ABC Discussion Prompt";
    - lines 924–928 commit message "Implementation plan extended based on code review findings";
    - lines 934–959 "Detailed Code Review Process".
  - Lines 866–875 (`/implementation_approve`) and 895–923 (`/implementation_new_tasks`, prompt body) → links only.

### `pr-creation.md`

- **Labels:** `status-08:ready-pr` (bot_pickup) → `status-09:pr-creating` (bot_busy) → `status-10:pr-created`.
- **Actor:** fully automated — coordinator dispatches `create-pr` on Jenkins.
- **Slash commands:** none for the bot. The failure labels auto-launch `/check_branch_status`.
- **Failure exits:** recovery for all three labels: fix the cause, then `mcp-coder gh-tool set-status status-08:ready-pr`.

  | Label | Cause |
  |---|---|
  | `status-09f:pr-creating-failed` | Any other error or crash |
  | `status-09f-timeout:pr-creating-llm-timeout` | LLM timeout during summary generation |
  | `status-09f-mcp:pr-creating-mcp-unavailable` | MCP server(s) failed to connect |

  Source: `src/mcp_coder/workflows/create_pr/core.py`.
- **Prompts:**
  - Line 1001 → keep the `PR Summary Generation` prompts.md link.
  - Lines 1005–1074 "Detailed PR Creation Process (Manual Reference)", including the Task Status Tracker template → move verbatim into "Additional prompt details".

### `pr-merge.md`

- **Labels:** `status-10:pr-created` (human_action) → merged and closed. GitHub closes the linked issue.
- **Actor:** human required — the only strictly human step. `status-10` has no auto-launched command.
- **Slash commands:** `/check_branch_status` (optional pre-merge check).
- **Key steps** (from lines 1111–1117), as a short list:
  - final review;
  - CI green;
  - merge.
  - Major rework → add tasks and set `status-05:plan-ready`.
- **Failure exits:** "None — human stage." Conflicts, CI and review comments while waiting are handled by PR follow-up; step 3 adds that link.

## HOW

Pure Markdown. Same layout as step 1.

## ALGORITHM

Same as step 1: skill blocks → links, everything else → verbatim under "Additional prompt details".

## DATA

Not applicable.

## Checks

- `check_file_size` (`max_lines=750`): the new files are not listed.
- Run `tools/lychee_check.bat` via Bash: 0 errors (fix broken links before committing).
- Every slash command named exists under `.claude/skills/`. If one is missing, write one line to `pr_info/.blocked.txt` and stop.
- Format, then commit: `docs(processes): add code-review, pr-creation, pr-merge docs`.
