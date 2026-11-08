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

### Step 1: Contract shim and strict `[tool.mcp-coder.toolkit]` config loading
See [step_1.md](./steps/step_1.md)

- [x] Implementation: `utils/toolkit.py` shim, strict `load_toml`, `toolkit_runner` config part, `.importlinter`, `pyproject.toml`, docs rows (tests first in `tests/utils/test_toolkit_config.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Toolkit registry and runner
See [step_2.md](./steps/step_2.md)

- [x] Implementation: `load_toolkit`, `run_request`, `run_binding`, `verify_toolkit`, `get_fragment` in `toolkit_runner` (tests first in `tests/utils/test_toolkit_runner.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Formatting through the `commit` binding
See [step_3.md](./steps/step_3.md)

- [x] Implementation: rewire `check_formatter_config` / `run_formatters` in `workflow_steps/commit.py`, update `tach.toml`, conftest fixture and affected tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Toolkit rows in `mcp-coder verify`
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: `_toolkit_rows` in `cli/commands/verify_sections.py` (tests first in `test_verify_project_section.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Implement's check loop through bindings
See [step_5.md](./steps/step_5.md)

- [ ] Implementation: `_run_check` and `entry` parameter in `task_processing.py`, binding gate in `core.py`, remove `RUN_MYPY_AFTER_EACH_TASK`, update tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Rebase checks through bindings, architecture cleanup
See [step_6.md](./steps/step_6.md)

- [ ] Implementation: `_run_all_checks` over `rebase` / `rebase_automated` bindings, `automated` flag in `rebase.py` / `rebase_automated.py`, `tach.toml`, architecture doc, update tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against base, address findings
- [ ] PR summary prepared
