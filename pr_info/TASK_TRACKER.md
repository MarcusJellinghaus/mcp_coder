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

- [x] [Step 1](./steps/step_1.md): Create shared `workflow_utils/failure_handling.py` with tests
- [x] [Step 2](./steps/step_2.md): Refactor implement workflow to use shared failure handling
- [x] [Step 3](./steps/step_3.md): Change `create_pull_request()` return type to `PullRequestData | None`
- [ ] [Step 4](./steps/step_4.md): Make pre-PR push fatal + add failure handling to create-pr workflow

## Pull Request
