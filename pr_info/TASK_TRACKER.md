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

- [x] [Step 1 — Dependencies + narrow import-linter contract](./steps/step_1.md)
- [x] [Step 2 — JSONC preprocessor (`_strip_jsonc`)](./steps/step_2.md)
- [x] [Step 3 — Schema: token map, builder, validation, gated emit](./steps/step_3.md)
- [x] [Step 4 — Layer discovery (`_discover_layers`)](./steps/step_4.md)
- [x] [Step 5 — Per-layer load (`_load_layer`)](./steps/step_5.md)
- [ ] [Step 6 — Public `load_permission_config` (merge + degrade + provenance)](./steps/step_6.md)

## Pull Request
