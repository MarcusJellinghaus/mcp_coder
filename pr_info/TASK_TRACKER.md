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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

- [x] [Step 1 — Shared check wrappers: `run_pytest_check` + `run_pylint_check`](./steps/step_1.md)
- [x] [Step 2 — Failure keys, `CheckRunError`, `_run_all_checks`](./steps/step_2.md)
- [x] [Step 3 — Git conflict helpers](./steps/step_3.md)
- [x] [Step 4 — New prompts + permission pruning](./steps/step_4.md)
- [x] [Step 5 — LLM session helper + prompt builders](./steps/step_5.md)
- [ ] [Step 6 — Orchestrator rewrite, marker-machinery removal, OUTPUT logging](./steps/step_6.md)

## Pull Request
