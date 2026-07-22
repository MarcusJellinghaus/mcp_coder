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

### Step 1: Scaffold the `workflow_steps` layer

Create the empty `mcp_coder.workflow_steps` package with `py.typed`, register it in
`.importlinter` and `tach.toml`, and add the `tests/workflow_steps/` scaffold tests.
See [step_1.md](./steps/step_1.md).

- [x] Implementation (scaffold tests + package files + enforcer config; `run_lint_imports_check` + `run_tach_check` green)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `refactor(workflow_steps): scaffold workflow_steps layer + register enforcers`

### Step 2: Move commit / push / run_formatters into `workflow_steps`

Move `run_formatters`, `commit_changes`, `push_changes` + `PR_INFO_DIR` /
`COMMIT_MESSAGE_FILE` into `workflow_steps`; repoint consumers and re-export constants.
See [step_2.md](./steps/step_2.md).

- [x] Implementation (move 3 funcs + 2 constants, repoint imports, relocate tests to `test_commit.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `refactor(workflow_steps): move commit/push/run_formatters + commit constants`

### Step 3: Move rebase into `workflow_steps`

Move `_get_rebase_target_branch` / `_attempt_rebase_and_push` into `workflow_steps`,
relocate all rebase test classes, and remove `implement/rebase.py`. Depends on Step 2.
See [step_3.md](./steps/step_3.md).

- [x] Implementation (move rebase funcs, repoint core.py, relocate all test classes to `test_rebase.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `refactor(workflow_steps): move rebase step`

### Step 4: Move CI check/fix into `workflow_steps` (loop-ready)

Move `check_and_fix_ci`, its helpers, `CIFixConfig` + 7 CI constants; add the three
defaulted keyword params; repoint both production consumers. Depends on Step 2.
See [step_4.md](./steps/step_4.md).

- [x] Implementation (move CI step + constants, add loop-ready params, repoint core.py + check_branch_status.py, relocate tests to `test_ci.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `refactor(workflow_steps): move CI step with loop-ready params + CI constants`

### Step 5: Extract shared `check_git_clean` prerequisite step

Create `workflow_steps/prerequisites.py` with shared `check_git_clean`; delegate from
`implement/prerequisites.py` and `create_pr/core.py`. Independent of Step 6.
See [step_5.md](./steps/step_5.md).

- [x] Implementation (shared `check_git_clean`, delegate both callers, tests in `test_prerequisites.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `refactor(workflow_steps): extract shared check_git_clean prerequisite`

### Step 6: Extract shared `is_branch_not_base` prerequisite step

Add pure-comparison `is_branch_not_base` to `workflow_steps/prerequisites.py`; delegate
from `implement`'s `check_main_branch` and `create_pr`'s branch check. Independent of Step 5.
See [step_6.md](./steps/step_6.md).

- [x] Implementation (pure-comparison helper, delegate both callers keeping their resolvers, add tests)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `refactor(workflow_steps): extract shared is_branch_not_base prerequisite`

## Pull Request

- [ ] Address PR review feedback
- [ ] Write PR summary
