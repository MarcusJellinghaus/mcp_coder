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

- [ ] [Step 1: Autofix formatting](./steps/step_1.md) — `ruff check --fix` (~75 fixes)
- [ ] [Step 2: Small manual fixes](./steps/step_2.md) — D100, D101, D103, D403, D415, D417, DOC102, DOC202 (~35)
- [ ] [Step 3: Missing test method docstrings](./steps/step_3.md) — D102 (~109)
- [ ] [Step 4: Missing Returns/Yields](./steps/step_4.md) — DOC201, DOC402 (~175)
- [ ] [Step 5: Fix Raises sections](./steps/step_5.md) — DOC501, DOC502 (~95)

## Pull Request
