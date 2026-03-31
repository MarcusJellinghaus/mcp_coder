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

### Step 1: Add `checkout-issue-branch` subcommand ([step_1.md](./steps/step_1.md))

Handler function, parser wiring, dispatch, and all tests (unit + integration).

- [x] Implementation: add `execute_checkout_issue_branch()` to `gh_tool.py`, subparser in `parsers.py`, dispatch + import in `main.py`, all tests in `test_gh_tool.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Skill file + settings update ([step_2.md](./steps/step_2.md))

Create `implement_direct` skill and add permissions to settings.

- [x] Implementation: create `.claude/skills/implement_direct/SKILL.md`, add `Skill(implement_direct)` to settings, update `gh-tool` permission to wildcard
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: verify all steps implemented correctly
- [ ] PR summary prepared
