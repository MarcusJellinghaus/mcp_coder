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

### Step 1: `format_best_effort` helper and the autouse `formatter_mocks` fixture
See [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 2: formatter-stable `write_round_log`
See [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 3: blank lines in `TASK_TRACKER_TEMPLATE`
See [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 4: Linux create-plan and review-plan templates run `mcp-coder setup`
See [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 5: create-plan formatter pre-flight and formatted plan commit
See [step_5.md](./steps/step_5.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 6: task tracker preparation formats and commits the formatter's changes
See [step_6.md](./steps/step_6.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 7: finalisation formats before its commit
See [step_7.md](./steps/step_7.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 8: the review's whole-tree round-log flush formats first
See [step_8.md](./steps/step_8.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 9: formatted commit before the CI gate on a dismiss round
See [step_9.md](./steps/step_9.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 10: "applied" ignores review logs and is measured before `_after_steps`
See [step_10.md](./steps/step_10.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

### Step 11: docs: formatting users, pre-flight list, failure behaviour
See [step_11.md](./steps/step_11.md)

- [ ] Implementation (docs)
- [ ] Quality checks (pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: check the full branch diff against `summary.md` and all steps
- [ ] PR summary prepared
