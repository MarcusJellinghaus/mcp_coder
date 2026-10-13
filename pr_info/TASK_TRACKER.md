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

### Step 1: Base-branch source and missing-base helper
See [step_1.md](./steps/step_1.md)

- [x] Implementation: `BaseBranchSource`, `detect_base_branch_with_source`, `check_base_branch_on_origin` with tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `mcp-coder rebase` trusts an issue-named base and checks it exists
See [step_2.md](./steps/step_2.md)

- [x] Implementation: `_resolve_base_branch` uses source, origin guard in `run_rebase_workflow`, `--base-branch` help text, with tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: create-plan checks the base branch before creating a branch
See [step_3.md](./steps/step_3.md)

- [x] Implementation: `BaseBranchMissingError` in `manage_branch`, failure handling in `core.py`, with tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: create-pr checks the base branch before opening the PR
See [step_4.md](./steps/step_4.md)

- [x] Implementation: origin check in `create_pull_request`, with tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Implement workflow's rebase step checks the base branch
See [step_5.md](./steps/step_5.md)

- [x] Implementation: warn and skip in `_attempt_rebase_and_push` on missing base, with tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: `gh-tool get-base-branch` handles failed detection and documents the real order
See [step_6.md](./steps/step_6.md)

- [x] Implementation: `None` check, warning text and docstring order in `execute_get_base_branch`, with tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 7: Document the epic-branch procedure and fix the CLI reference
See [step_7.md](./steps/step_7.md)

- [x] Implementation: update `docs/cli-reference.md` and `docs/repository-setup/github.md` (Epic Branches section)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review all changes against `pr_info/steps/summary.md`
- [ ] PR summary prepared
