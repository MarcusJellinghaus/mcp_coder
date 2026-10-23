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

### Step 1: Replace DEP002 list with `optional_dependencies_dev_groups`
See [step_1.md](./steps/step_1.md)

- [ ] Implementation: add `optional_dependencies_dev_groups` to `[tool.deptry]`, remove the `DEP002` ignore list, update `docs/repository-setup/python.md`, verify with `deptry src`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review all changes against the summary and step files
- [ ] PR summary prepared
