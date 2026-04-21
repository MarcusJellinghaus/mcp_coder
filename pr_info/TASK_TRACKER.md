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

### Step 1: Create shim `mcp_workspace_github.py` + smoke tests
- [ ] Implementation: create shim module and smoke tests ([step_1.md](./steps/step_1.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Relocate `label_config.py` to `config/` package
- [ ] Implementation: move label_config.py and update all imports ([step_2.md](./steps/step_2.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Build `label_transitions.py` + migrate label update tests
- [ ] Implementation: extract standalone update_workflow_label function and migrate tests ([step_3.md](./steps/step_3.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Update all consumer imports to use shim
- [ ] Implementation: switch all github_operations imports to mcp_workspace_github ([step_4.md](./steps/step_4.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Update `update_workflow_label` call sites
- [ ] Implementation: switch 4 call sites to standalone function ([step_5.md](./steps/step_5.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Delete local `github_operations/` + old tests
- [ ] Implementation: delete src and test directories, verify no remaining imports ([step_6.md](./steps/step_6.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Update `.importlinter` and `tach.toml`
- [ ] Implementation: update architecture configs for github shim ([step_7.md](./steps/step_7.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps complete and checks pass
- [ ] PR summary prepared
