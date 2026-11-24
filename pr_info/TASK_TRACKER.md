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

### Step 1: Build the `check_instructions` re-run list from the session's Bash grants
See [step_1.md](./steps/step_1.md)

- [x] Implementation: tests first (`test_prompt_slots.py`, `test_interface_prompt_slots.py`, `test_toolkit_describe.py`), then `RERUN_INTRO` + grant-based re-run list in `utils/prompt_slots.py` and `check_instructions` fragment always `""` in `toolkits/command/toolkit.py`
- [x] Quality checks (pylint, pytest, mypy, lint-imports) — fix all issues
- [x] Commit message prepared

### Step 2: Scope each session's Bash grants to its binding entries
See [step_2.md](./steps/step_2.md)

- [x] Implementation: tests first (task processing, finalisation, CI, check loop, acceptance in `test_toolkit_permissions.py`), then per-entry `llm_permissions` calls in `task_processing.py`, `finalisation.py`, `workflow_steps/ci.py` and `_fix_turn(entry=...)` in `check_loop.py`
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 3: `verify` rows for declared toolkit depths
See [step_3.md](./steps/step_3.md)

- [x] Implementation: tests first (`test_toolkit_runner.py`, `test_verify_toolkit_rows.py`), then `can_request` in `utils/toolkit_runner.py` and declared-depth rows (`_ran_by`, `_declared_row`) in `cli/commands/verify_toolkit_rows.py`
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 4: Docs — npm example and per-session grant scope
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: trim npm example and rewrite the "Which sessions." bullet in `docs/configuration/toolkits.md`
- [ ] Quality checks (pytest in case a test reads the docs) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch
- [ ] PR summary prepared
