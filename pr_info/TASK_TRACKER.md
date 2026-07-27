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

- [x] [Step 1: Shared primitives — llm_failure_reason + run_guarded](./steps/step_1.md)
- [x] [Step 2: Migrate implement onto run_guarded (pure refactor)](./steps/step_2.md)
- [ ] [Step 3: Migrate create-plan + add planning_mcp label](./steps/step_3.md)
- [ ] [Step 4: Migrate create-pr + add pr_creating_timeout / pr_creating_mcp](./steps/step_4.md)
- [ ] [Step 5: Enhance review (guard + broadened excepts + empty-report retry)](./steps/step_5.md)

## Pull Request
