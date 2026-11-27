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

### Step 1: create-plan logs steps 4-6 when each prompt starts
See [step_1.md](./steps/step_1.md)

- [x] Implementation: ordering test in `test_prompt_execution.py`, move Step 4/5/6 lines into `run_planning_prompts` (`core.py` must not grow)
- [x] Quality checks: format, pylint, mypy, pytest (fast unit set) — fix all issues
- [x] Commit message prepared

### Step 2: rebase skips the force-push when HEAD already equals origin/<branch>
See [step_2.md](./steps/step_2.md)

- [x] Implementation: `TestUpToDate` tests, in-place edits to `test_rebase.py`, `_up_to_date_branch` helper and call in `_attempt_rebase_and_push`, docstring/comment updates in `rebase.py` and `review/steps.py`
- [x] Quality checks: format, pylint, mypy, pytest (fast unit set + `git_integration`) — fix all issues
- [x] Commit message prepared

### Step 3: check loop logs each request with status, duration and summary (INFO)
See [step_3.md](./steps/step_3.md)

- [x] Implementation: `TestRequestLogging` tests, `_SUMMARY_MAX` / `_one_line` and `_run_group` logging in `check_loop.py`, fix-loop bullet in `docs/architecture/toolkit-interface.md`
- [x] Quality checks: format, pylint, mypy, pytest (fast unit set) — fix all issues
- [x] Commit message prepared

### Step 4: command toolkit steps log what they ran (DEBUG)
See [step_4.md](./steps/step_4.md)

- [x] Implementation: `TestStepLogging` and `caplog` assertions in `TestFailures`, DEBUG lines and timing in `_run_step`
- [x] Quality checks: format, pylint, mypy, pytest (fast unit set) — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
