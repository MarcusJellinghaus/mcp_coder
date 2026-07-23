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

### Step 1: Least-privilege permissions constant ([step_1.md](./steps/step_1.md))

- [ ] Implementation: `REBASE_LLM_PERMISSIONS` constant + tests (`test_rebase_permissions.py`, `__init__.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Automated Rebase prompt + drift test ([step_2.md](./steps/step_2.md))

- [ ] Implementation: add `## Automated Rebase` to `prompts.md` + `test_prompt.py` (loader + SKILL-drift test)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Pure decision logic ([step_3.md](./steps/step_3.md))

- [ ] Implementation: `_parse_outcome_marker` + `_evaluate_pre_push` in `rebase.py` + `test_decision.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Low-level git helpers ([step_4.md](./steps/step_4.md))

- [ ] Implementation: `_run_git`, `_is_rebase_in_progress`, `_abort_rebase`, `_reset_hard`, `_rebase_success_shape` + `test_git_helpers.py`
- [ ] Quality checks: pylint, pytest, mypy, bandit — fix all issues
- [ ] Commit message prepared

### Step 5: Guards (pre-flight, base-branch, pr_info-on-base) ([step_5.md](./steps/step_5.md))

- [ ] Implementation: `_preflight`, `_resolve_base_branch`, `_check_pr_info_absent_on_base` + `test_guards.py`
- [ ] Quality checks: pylint, pytest, mypy, bandit — fix all issues
- [ ] Commit message prepared

### Step 6: Orchestrator `run_rebase_workflow` ([step_6.md](./steps/step_6.md))

- [ ] Implementation: `run_rebase_workflow` + `_run_rebase_session` + `test_workflow.py` (mocked LLM/git)
- [ ] Quality checks: pylint, pytest, mypy, bandit — fix all issues
- [ ] Commit message prepared

### Step 7: CLI wiring ([step_7.md](./steps/step_7.md))

- [ ] Implementation: `command_catalog`, `add_rebase_parser`, `execute_rebase` + `_resolve_rebase_settings`, `main.py` route + `test_rebase.py` (and `test_help_anti_drift.py` if needed)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Address PR review feedback
- [ ] Write PR summary
