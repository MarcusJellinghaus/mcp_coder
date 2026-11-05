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

### Step 1: Import contract and one-off check

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation: add `quality_tools_isolation` contract to `.importlinter`, run the one-off check with the throwaway module, delete the module
- [x] Quality checks: lint-imports, pylint, pytest, mypy — fix all issues
- [x] Commit message prepared in `pr_info/.commit_message.txt`, with the one-off check result as observed

### Step 2: Subprocess rule, tests and docs

Details: [step_2.md](./steps/step_2.md)

- [ ] Implementation: add the failing test, then the `quality-tools` rule, update docstring, script comments and docs, run the `src/` probe and delete `.scratch/`
- [ ] Quality checks: pylint, pytest, mypy, ruff — fix all issues
- [ ] Commit message prepared in `pr_info/.commit_message.txt`

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary: prepare the pull request title and description
