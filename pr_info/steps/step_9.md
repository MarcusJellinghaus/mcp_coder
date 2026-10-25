# Step 9 — Cheat sheet update

## LLM prompt

> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_9.md`).
> Update `docs/processes-prompts/claude_cheat_sheet.md`:
> - add the PR follow-up step to "General Process";
> - note the failure-label entry command;
> - remove `/clear`.
> Do not touch `refactoring-guide.md`.
> Format, then commit as one commit.

## WHERE

```
docs/processes-prompts/claude_cheat_sheet.md
```

## WHAT

1. **"General Process":** insert before "Merge PR".
   ```
   4. **PR follow-up (while the PR waits at status-10):**
      merge conflict → bot `fix-conflict`; failing CI → bot `fix-ci`;
      review comments → `/pr_comment_triage`
      > 🤖 *bot: mcp-coder coordinate → `fix-conflict` / `fix-ci`*
   5. **Merge PR:** Review and merge in GitHub
   ```
2. **New short section "Failure labels":** `/check_branch_status` is the entry command for every failure label. Exception: `status-17f-tasks` uses `/implementation_finalise`. Link to [failure-handling.md](processes/failure-handling.md).
3. **"Plan Review" decision line:** replace `/clear` with "clear the context". `/clear` is not a skill under `.claude/skills/`.
4. **Overview table:** add `/plan_review_supervisor` and `/issue_analyse_supervisor`. Both exist as skills and are named in the per-process docs.
5. Line 5 link stays `development-process.md` (still valid).

## HOW / ALGORITHM / DATA

Markdown only, so there is no algorithm or data.

## Checks

- Every slash command in the file exists under `.claude/skills/`.
- Run `tools/lychee_check.bat` via Bash: 0 errors.
- `check_file_size` (`max_lines=750`): nothing flagged.
- Run the fast unit pytest suite (from CLAUDE.md) once more as the final check.
- Format, then commit: `docs(cheat-sheet): add PR follow-up and failure-label entry command`.
