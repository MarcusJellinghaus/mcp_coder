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

### src/ (Steps 1-8)
- [x] [Step 1: src/ W0611 — unused imports (36)](./steps/step_1.md)
- [x] [Step 2: src/ W0612 — unused variables (5)](./steps/step_2.md)
- [x] [Step 3: src/ W0613 + W1309 — unused args + bare f-string (9)](./steps/step_3.md)
- [x] [Step 4: src/ W0707 + W0719 — raise-missing-from + broad-exception-raised (8)](./steps/step_4.md)
- [x] [Step 5: src/ W0706 + W4903 — try-except-raise + deprecated arg (4)](./steps/step_5.md)
- [x] [Step 6: src/ W0603 — global-statement (7)](./steps/step_6.md)
- [ ] [Step 7: src/ W0212 — protected-access (11)](./steps/step_7.md)
- [ ] [Step 8: src/ W0718 — broad-exception-caught (181)](./steps/step_8.md)

### tests/ (Steps 9-13)
- [ ] [Step 9: tests/ W0612 — unused variables (43)](./steps/step_9.md)
- [ ] [Step 10: tests/ W1514 — unspecified encoding (23)](./steps/step_10.md)
- [ ] [Step 11: tests/ W0718 — broad-exception-caught (31)](./steps/step_11.md)
- [ ] [Step 12: tests/ W0107 + W0108 + W0702 + W0719 — small mechanical fixes (10)](./steps/step_12.md)
- [ ] [Step 13: tests/ W1404 + W0201 — string concat + attribute-outside-init (6)](./steps/step_13.md)

### Config (Step 14 — LAST)
- [ ] [Step 14: pyproject.toml config change](./steps/step_14.md)

## Pull Request
