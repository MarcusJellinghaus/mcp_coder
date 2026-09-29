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

- [x] [Step 1](./steps/step_1.md) — Model: `Rule.ref`, `Rule.matcher` widening, `origin` `compare=False`, 4 skip guards
- [x] [Step 2](./steps/step_2.md) — `permissions/expand.py` + import-linter contracts + export
- [x] [Step 3](./steps/step_3.md) — Loader two-phase + `@group` expansion for config rules
- [x] [Step 4](./steps/step_4.md) — `toolScenarios` shape (`ScenarioBlock` + schema)
- [ ] [Step 5](./steps/step_5.md) — `skill_frame`: `@ref` lookup + `use:` substitution
- [ ] [Step 6](./steps/step_6.md) — CLI wiring: D9 load hoist, D12 banner gating

## Pull Request
