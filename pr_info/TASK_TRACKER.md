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

### Step 1: Enhance `branch_manager.py` — Core Resolution Logic ([step_1.md](./steps/step_1.md))

- [x] Part A: Generalize `_extract_open_prs()` → `_extract_prs_by_states()` — write tests and implement
- [x] Part A: Run pylint, pytest, mypy — fix all issues
- [x] Part A: Prepare git commit message
- [x] Part B: Add `_search_branches_by_pattern()` method — write tests and implement
- [x] Part B: Run pylint, pytest, mypy — fix all issues
- [x] Part B: Prepare git commit message
- [x] Part C: Extend `get_branch_with_pr_fallback()` with closed-PR and pattern-search steps — write tests and implement
- [x] Part C: Run pylint, pytest, mypy — fix all issues
- [x] Part C: Prepare git commit message

### Step 2: Remove `get_linked_branch_for_issue()` Wrapper, Update All Callers ([step_2.md](./steps/step_2.md))

- [x] Part A: Delete `get_linked_branch_for_issue()` and update `issues.py` — write tests and implement
- [x] Part A: Run pylint, pytest, mypy — fix all issues
- [x] Part A: Prepare git commit message
- [x] Part B: Update `session_launch.py` (`process_eligible_issues`) — write tests and implement
- [x] Part B: Run pylint, pytest, mypy — fix all issues
- [x] Part B: Prepare git commit message
- [x] Part C: Update `session_restart.py` (`_prepare_restart_branch`) — write tests and implement
- [x] Part C: Run pylint, pytest, mypy — fix all issues
- [x] Part C: Prepare git commit message
- [x] Part D: Update `commands.py` (`_handle_intervention_mode`) — fix latent bug — write tests and implement
- [x] Part D: Run pylint, pytest, mypy — fix all issues
- [x] Part D: Prepare git commit message

### Step 3: Verify and Fix Remaining Tests Across All Suites ([step_3.md](./steps/step_3.md))

- [ ] Part A: Run full unit test suite (excluding integration tests)
- [ ] Part B: Fix any remaining test failures (stale mocks, imports, ValueError assertions, missing params)
- [ ] Part B: Run pylint, pytest, mypy — fix all issues
- [ ] Part B: Prepare git commit message
- [ ] Part C: Re-run full test suite — verify all tests pass
- [ ] Part D: Run pylint and mypy final checks — fix any issues
- [ ] Part D: Prepare git commit message

## Pull Request

- [ ] Review all changes across steps 1–3 for consistency and completeness
- [ ] Verify no references to `get_linked_branch_for_issue` remain in codebase
- [ ] Run full test suite one final time — all green
- [ ] Prepare PR title and summary
