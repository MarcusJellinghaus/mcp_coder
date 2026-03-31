# Step 10: Delete Old .claude/commands/ Directory

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Remove the old `.claude/commands/` directory after verifying all 18 skills have been successfully migrated to `.claude/skills/`.

## LLM Prompt

```
Read summary.md and this step file.

Delete the .claude/commands/ directory and all its contents.
```

## WHERE

| Action | Path |
|--------|------|
| **Delete** | `.claude/commands/` (entire directory) |

## WHAT — Files to Delete

All 19 files in `.claude/commands/`:
- `check_branch_status.md`
- `commit_push.md`
- `discuss.md`
- `implementation_approve.md`
- `implementation_finalise.md`
- `implementation_needs_rework.md`
- `implementation_new_tasks.md`
- `implementation_review.md`
- `implementation_review_supervisor.md`
- `issue_analyse.md`
- `issue_approve.md`
- `issue_create.md`
- `issue_update.md`
- `plan_approve.md`
- `plan_review.md`
- `plan_review_supervisor.md`
- `plan_update.md`
- `rebase.md`
- `rebase_design.md.txt`

## HOW

1. Delete `.claude/commands/` directory and all contents
2. Run `git status` to verify only the expected deletions appear

## ALGORITHM

```
delete_directory(.claude/commands/)
git status  # should show 19 deleted files
```

## DATA

- Input: Verification of 21 target files
- Output: 19 deleted files from `.claude/commands/`

## Commit Message

```
chore: remove old commands directory after skills migration

All 18 commands successfully migrated to .claude/skills/.
Delete .claude/commands/ directory (18 .md files + rebase_design.md.txt).
```
