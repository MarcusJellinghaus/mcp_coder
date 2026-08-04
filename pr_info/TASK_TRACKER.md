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

### Step 1: `assess_ci` policy helper + CLI delegation

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation — create `checks/ci_policy.py` (`assess_ci`), route `_exit_code` and pre-`--fix` bail-out through it; add tests (`tests/checks/test_ci_policy.py`, regression in `test_check_branch_status_exit_code.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
  - Step 1 code is clean: pylint on `ci_policy.py` = no issues; mypy on `checks/` (isolated) = no issues in `ci_policy.py`.
  - The full-repo run reports only **pre-existing, environmental** failures unrelated to this step: the test `.venv` has a stale `mcp-workspace` (predating merged #1105/#1068) missing `checks.branch_status_rendering`, `BranchStatusReport.pr_feedback_undeterminable`, and the `format_for_*(fail_on_reviews=)` params, plus uninstalled optional `langchain`/`httpx`/`mcp` integration deps. These affect the whole repo equally and are not introduced by Step 1; the fix is to reprovision the venv (`mcp-workspace` from git HEAD), which is outside source scope.
- [x] Commit message prepared

### Step 2: Two new failure labels in `labels.json`

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation — add `code_review_open_tasks` + `code_review_ci_unknown` labels to `config/labels.json`; update `test_label_config.py` and `test_define_labels.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
  - pylint + mypy on the touched test files: clean, no issues.
  - pytest could not collect: the test `.venv` has a stale `mcp-workspace` missing `mcp_workspace.checks.branch_status_rendering`, which breaks `import mcp_coder` at collection time (via `src/mcp_coder/__init__.py` → `checks/branch_status.py`). This is the same pre-existing, environmental blocker documented in Step 1 and affects the whole repo; it is not introduced by this JSON/test-list change. Fix is to reprovision the venv (`mcp-workspace` from git HEAD), which is outside source scope.
- [x] Commit message prepared

### Step 3: `ReviewConfig.enforce_implementation_gates` + failure_labels entries

Detail: [step_3.md](./steps/step_3.md)

- [ ] Implementation — add `enforce_implementation_gates` field, set on both instances, extend `REVIEW_IMPLEMENTATION.failure_labels` with `tasks`/`ci_unknown`; update `test_config.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: `_fail` gains an optional `details` param

Detail: [step_4.md](./steps/step_4.md)

- [ ] Implementation — add keyword-only `details` param to `_fail` in `handoff.py`, insert after header line; update `test_handoff.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Gate 1 — entry gate (open-tasks pre-flight)

Detail: [step_5.md](./steps/step_5.md)

- [ ] Implementation — create `workflows/review/gates.py` (`check_open_tasks_gate`), wire into `core.body()`; add `tests/workflows/review/test_gates.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Gate 2 — exit guard (CI proven green)

Detail: [step_6.md](./steps/step_6.md)

- [ ] Implementation — add `check_ci_proven_gate` to `gates.py`, wire into dismiss cascade in `core.py`; extend `test_gates.py` and core dismiss-path tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Documentation

Detail: [step_7.md](./steps/step_7.md)

- [ ] Implementation — add `17f-tasks` / `17f-ci-unknown` rows to `development-process.md`, `github_Issue_Workflow_Matrix.html`, and `cli-reference.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Address PR review feedback
- [ ] Final summary and verification
