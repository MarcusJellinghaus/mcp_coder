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

### Step 1: Split `src/mcp_coder/cli/parsers.py` into three modules — [step_1.md](./steps/step_1.md)
- [ ] Implementation: move workflow/interactive parser functions to `workflow_parsers.py` / `interactive_parsers.py`, update `main.py` imports, `command_catalog.py` docstring, `.large-files-allowlist`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Split `tests/cli/test_parsers.py` to mirror the parser modules — [step_2.md](./steps/step_2.md)
- [ ] Implementation: move test classes to `test_workflow_parsers.py`, `test_interactive_parsers.py`, `test_gh_parsers.py`; verify collect counts
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Split `tests/cli/test_main.py` — [step_3.md](./steps/step_3.md)
- [ ] Implementation: move coordinator tests to `test_main_coordinator.py`, parser tests to `test_parsers.py`, update `.large-files-allowlist`; verify collect counts
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review full branch diff against `main`
- [ ] PR summary prepared
