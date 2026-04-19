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

### Step 1: Add `ImplementConfig` and `get_implement_config()` to pyproject_config.py
- [x] Implementation: add `ImplementConfig` dataclass and `get_implement_config()` function with tests ([step_1.md](./steps/step_1.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Gate formatting and mypy in task_processing.py
- [x] Implementation: add `format_code`/`check_type_hints` params to `process_single_task()` and `process_task_with_retry()`, gate Steps 7-8, update existing tests ([step_2.md](./steps/step_2.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Read config in core.py and pass booleans down
- [x] Implementation: import and call `get_implement_config()` in `run_implement_workflow()`, pass config to `process_task_with_retry()`, gate Step 5 final mypy/formatting ([step_3.md](./steps/step_3.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Add PROJECT section to verify command
- [x] Implementation: add `_print_project_section()` to verify.py, call from `execute_verify()` after PROMPTS section ([step_4.md](./steps/step_4.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Add `[tool.mcp-coder.implement]` to pyproject.toml
- [x] Implementation: add `[tool.mcp-coder.implement]` section with `format_code = true` and `check_type_hints = true`, add verification test ([step_5.md](./steps/step_5.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request
- [x] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
