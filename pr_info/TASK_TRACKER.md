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

### Step 1: Logging Infrastructure — NOTICE→OUTPUT, CleanFormatter, setup_logging()
- [ ] Implementation: rename NOTICE→OUTPUT, add CleanFormatter, update setup_logging() formatter selection, update exports and tests ([step_1.md](./steps/step_1.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: CLI Defaults — --log-level choices, _resolve_log_level(), _INFO_COMMANDS
- [ ] Implementation: add OUTPUT to --log-level choices, shrink _INFO_COMMANDS to coordinator, update _resolve_log_level() default, update tests ([step_2.md](./steps/step_2.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: create-pr Workflow — Remove log_step(), Add PR Summary Fields
- [ ] Implementation: remove log_step(), replace call sites with logger.log(OUTPUT, ...), add PR summary fields, update tests ([step_3.md](./steps/step_3.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: CI Wait Progress and check_branch_status Print Migration
- [ ] Implementation: replace dot progress with periodic OUTPUT log messages, migrate print() calls to logging, update tests ([step_4.md](./steps/step_4.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Print Migration — Core CLI Commands
- [ ] Implementation: migrate status/error print() calls to logging across core CLI command files, keep data-producing prints ([step_5.md](./steps/step_5.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Print Migration — Coordinator and vscodeclaude Commands
- [ ] Implementation: migrate coordinator/vscodeclaude prints to logging, grep and fix all remaining NOTICE references across codebase ([step_6.md](./steps/step_6.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps complete, no remaining NOTICE refs, no stray print() calls
- [ ] PR summary prepared
