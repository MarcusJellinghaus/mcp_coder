# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

- [x] [Step 1](./steps/step_1.md) — Migrate simple skills: discuss, plan_approve, implementation_approve, implementation_needs_rework
- [x] [Step 2](./steps/step_2.md) — Migrate issue_create, issue_update, plan_update
- [x] [Step 3](./steps/step_3.md) — Migrate skills with dynamic context injection: issue_analyse, issue_approve, check_branch_status
- [x] [Step 4](./steps/step_4.md) — Migrate plan_review, implementation_review, implementation_finalise
- [x] [Step 5](./steps/step_5.md) — Migrate implementation_new_tasks, commit_push
- [x] [Step 6](./steps/step_6.md) — Migrate rebase + move rebase_design.md
- [x] [Step 7](./steps/step_7.md) — Migrate plan_review_supervisor + extract supervisor_workflow.md
- [ ] [Step 8](./steps/step_8.md) — Migrate implementation_review_supervisor + extract supervisor_workflow.md
- [ ] [Step 9](./steps/step_9.md) — Update settings.local.json + documentation
- [ ] [Step 10](./steps/step_10.md) — Delete old .claude/commands/ directory

## Pull Request
