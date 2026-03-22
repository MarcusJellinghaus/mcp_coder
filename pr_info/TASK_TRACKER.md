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

### Phase 1 — Initial pass (partially complete)

- [x] [Step 1: Autofix formatting](./steps/step_1.md) — `ruff check --fix` (~75 fixes)
- [x] [Step 2: Small manual fixes](./steps/step_2.md) — D100, D101, D103, D403, D415, D417, DOC102, DOC202 (~35)
- ~~[Step 3: Removed](./steps/step_3.md) — tests/ excluded from scope~~
- [x] [Step 4: Missing Returns/Yields](./steps/step_4.md) — DOC201, DOC402, `src/` only (~101)
- [x] [Step 5: Fix Raises sections](./steps/step_5.md) — DOC501, DOC502, `src/` only (~86)

### Phase 2 — Cleanup (~102 remaining violations)

- [x] [Step 6: Re-run autofix formatting](./steps/step_6.md) — D212, D202 (~28)
- [x] [Step 7: Small manual fixes](./steps/step_7.md) — D301, D417, D205, D415, DOC102 (~11)
- [x] [Step 8: Missing Returns batch 1](./steps/step_8.md) — DOC201 in cli, config, formatters, checks (~16)
- [x] [Step 9: Missing Returns batch 2](./steps/step_9.md) — DOC201 in llm, utils, workflows (~16)
- [ ] [Step 10: Remove extraneous Raises](./steps/step_10.md) — DOC502 (~20)
- [ ] [Step 11: Add missing Raises](./steps/step_11.md) — DOC501 (~11), final step

## Pull Request
