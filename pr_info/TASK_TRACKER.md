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

### Step 1: Parse range keys strictly and reject overlaps
See [step_1.md](./steps/step_1.md)

- [ ] Implementation: tests in `TestExitCodes` (test_config.py), then `ExitCodes` alias, strict key parsing and overlap check in `config.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Look up exit codes by range, unlisted `0` is `ok`
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: tests in test_config.py and test_toolkit_run.py, then `exit_code_status` in `config.py` used by `toolkit.py::_run_step`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Document range keys and the unlisted-`0` rule
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: update `exit_codes` rows and add dependency-cruiser rule in `docs/configuration/toolkits.md`
- [ ] Quality checks: pytest — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main`, address findings
- [ ] PR summary prepared
