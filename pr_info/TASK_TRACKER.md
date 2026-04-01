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

- [x] [Step 1: Soft-Delete File I/O Helpers](./steps/step_1.md) — `helpers.py` + tests
- [x] [Step 2: Cleanup — Retry + Soft-Delete on Failure](./steps/step_2.md) — `cleanup.py` + caller + tests
- [x] [Step 3: Suffix-Aware Folder Naming](./steps/step_3.md) — `workspace.py` + tests
- [ ] [Step 4: Status Filtering](./steps/step_4.md) — `status.py` + caller + tests
- [ ] [Step 5: Session Lookup + Orphan Detection](./steps/step_5.md) — `sessions.py` + caller + tests

## Pull Request
