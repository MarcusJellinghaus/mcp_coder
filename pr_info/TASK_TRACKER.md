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

### Step 1: Add `build_url` and `elapsed_time` to `WorkflowFailure` Dataclass
- [x] Implementation: add two optional fields to `WorkflowFailure` in `constants.py` + tests in `test_constants.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(constants): add build_url and elapsed_time fields to WorkflowFailure (#598)`

### Step 2: Update `_format_failure_comment()` to Include Elapsed Time and Build URL
- [x] Implementation: add `_format_elapsed_time()` helper and update `_format_failure_comment()` in `core.py` + tests in `test_core.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(core): include elapsed time and build URL in failure comments (#598)`

### Step 3: Update Existing `WorkflowFailure(...)` Constructions with `build_url` and `elapsed_time`
- [x] Implementation: capture `start_time` and `build_url` at top of `run_implement_workflow()`, pass to every `WorkflowFailure(...)` in `core.py` + tests in `test_core.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(core): add build_url and elapsed_time to existing WorkflowFailure constructions (#598)`

### Step 4: Add `try/finally` Safety Net + SIGTERM Handler
- [x] Implementation: wrap workflow body in `try/finally`, add `reached_terminal_state` flag, register SIGTERM handler in `core.py` + tests in `test_core.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(core): add try/finally safety net and SIGTERM handler to implement workflow (#598)`

### Step 5: Add Heartbeat Support to `execute_subprocess()` and Pass from `ask_claude_code_cli()`
- [x] Implementation A: add `_run_heartbeat()` and heartbeat params to `execute_subprocess()` in `subprocess_runner.py` + tests in `test_subprocess_runner.py`
- [ ] Implementation B: add `LLM_HEARTBEAT_INTERVAL_SECONDS` constant and pass heartbeat params from `ask_claude_code_cli()` in `claude_code_cli.py` + tests in `test_claude_code_cli.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(subprocess): add heartbeat logging to execute_subprocess and enable for LLM calls (#598)`

### Step 6: Add Elapsed Time and Heartbeat to CI Polling Logs
- [ ] Implementation: add `poll_start_time`, elapsed time to debug logs, and INFO heartbeat every 8th iteration in `_poll_for_ci_completion()` in `core.py` + tests in `test_core.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(core): add elapsed time and heartbeat to CI polling logs (#598)`

## Pull Request
- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
