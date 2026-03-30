# Step 10: Delete Old .claude/commands/ Directory

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Remove the old `.claude/commands/` directory after verifying all 18 skills have been successfully migrated to `.claude/skills/`.

## LLM Prompt

```
Read summary.md and this step file.

1. Verify all 18 skill directories exist under .claude/skills/ with valid SKILL.md files
2. Verify the 3 supporting files exist (rebase/rebase_design.md, 2x supervisor_workflow.md)
3. Delete the entire .claude/commands/ directory (18 .md files + rebase_design.md.txt)
```

## WHERE

| Action | Path |
|--------|------|
| Verify exists | `.claude/skills/discuss/SKILL.md` |
| Verify exists | `.claude/skills/implementation_approve/SKILL.md` |
| Verify exists | `.claude/skills/implementation_needs_rework/SKILL.md` |
| Verify exists | `.claude/skills/plan_approve/SKILL.md` |
| Verify exists | `.claude/skills/issue_create/SKILL.md` |
| Verify exists | `.claude/skills/issue_update/SKILL.md` |
| Verify exists | `.claude/skills/plan_update/SKILL.md` |
| Verify exists | `.claude/skills/issue_analyse/SKILL.md` |
| Verify exists | `.claude/skills/issue_approve/SKILL.md` |
| Verify exists | `.claude/skills/check_branch_status/SKILL.md` |
| Verify exists | `.claude/skills/plan_review/SKILL.md` |
| Verify exists | `.claude/skills/implementation_review/SKILL.md` |
| Verify exists | `.claude/skills/implementation_finalise/SKILL.md` |
| Verify exists | `.claude/skills/implementation_new_tasks/SKILL.md` |
| Verify exists | `.claude/skills/commit_push/SKILL.md` |
| Verify exists | `.claude/skills/rebase/SKILL.md` |
| Verify exists | `.claude/skills/rebase/rebase_design.md` |
| Verify exists | `.claude/skills/plan_review_supervisor/SKILL.md` |
| Verify exists | `.claude/skills/plan_review_supervisor/supervisor_workflow.md` |
| Verify exists | `.claude/skills/implementation_review_supervisor/SKILL.md` |
| Verify exists | `.claude/skills/implementation_review_supervisor/supervisor_workflow.md` |
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

1. List `.claude/skills/` to verify all 18 directories exist
2. Spot-check a few SKILL.md files for valid YAML frontmatter
3. Delete `.claude/commands/` directory and all contents
4. Run `git status` to verify only the expected deletions appear

## ALGORITHM

```
# Verification
expected_skills = [list of 18 skill names]
for skill in expected_skills:
    assert exists(.claude/skills/{skill}/SKILL.md)
assert exists(.claude/skills/rebase/rebase_design.md)
assert exists(.claude/skills/plan_review_supervisor/supervisor_workflow.md)
assert exists(.claude/skills/implementation_review_supervisor/supervisor_workflow.md)

# Deletion
delete_directory(.claude/commands/)

# Post-check
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
