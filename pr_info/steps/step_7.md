# Step 7 — Documentation

**Read first:** `pr_info/steps/summary.md` (§ "Two new failure labels",
§ Constraints on the recovery column). Docs-only commit; no code, so quality
checks pass trivially. This records the two new statuses and their human-recovery
paths so a blocked run has a documented way back into the lane.

## WHERE

- **Modified:** `docs/processes-prompts/development-process.md`
- **Modified:** `docs/processes-prompts/github_Issue_Workflow_Matrix.html`
- **Modified:** `docs/cli-reference.md`

## WHAT / HOW

1. **`development-process.md`** (around the existing `17f-*` rows) — add two rows:
   - `status-17f-tasks:code-review-open-tasks` — recovery column (a `set-status`
     path, **not** just the label's `vscodeclaude.commands`):
     *"run `/implementation_finalise`, then
     `mcp-coder gh-tool set-status status-17:code-review-bot`"*.
   - `status-17f-ci-unknown:code-review-ci-undeterminable` — recovery:
     *"run `/check_branch_status` (check the GitHub token / whether CI exists),
     then `mcp-coder gh-tool set-status status-17:code-review-bot`"*.
   Note the precondition: enabling `auto_review_implementation` presumes the repo
   has CI (the lane leans on `check_and_fix_ci` for quality); a CI-less repo will
   end every review on `17f-ci-unknown`.

2. **`github_Issue_Workflow_Matrix.html`** — add the two new statuses alongside
   the other `17f-*` code-review failure statuses, matching the existing row
   markup.

3. **`cli-reference.md`** (near the existing code-review status list, ~line 464) —
   list the two new status names with a one-line description each.

## DATA

Documentation only. No signatures, no return values.

## Checks

pylint / pytest / mypy green (unaffected). No file-size regression.

## Commit

`Document code-review open-tasks and ci-undeterminable statuses`
