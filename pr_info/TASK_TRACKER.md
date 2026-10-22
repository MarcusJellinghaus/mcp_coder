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

### Step 1: Move checkout-issue-branch tests into their own file — [step_1.md](./steps/step_1.md)

- [x] Implementation: create `tests/cli/commands/test_gh_tool_checkout.py` with moved fixtures/classes, remove them from `test_gh_tool.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Resolve via PR fallback, pre-create checks, exit code 3 — [step_2.md](./steps/step_2.md)

- [x] Implementation: tests in `test_gh_tool_checkout.py` + `execute_checkout_issue_branch()` flow and `_find_precreate_candidates()` in `gh_tool.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Document resolution order and exit codes 0–3 — [step_3.md](./steps/step_3.md)

- [x] Implementation: epilog test + `gh_parsers.py` epilog, `docs/cli-reference.md`, `implement_direct/SKILL.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main`, address findings
- [ ] PR summary prepared
