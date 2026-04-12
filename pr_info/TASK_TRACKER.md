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

### Step 1: Add run_format_code shim + swap caller
- [ ] Implementation: add `run_format_code` shim to `mcp_tools_py.py`, swap import in `task_processing.py`, update tests, add `tach.toml` dependency
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared: `refactor: add run_format_code shim + swap caller`

### Step 2: Delete formatters package and update configs
- [ ] Implementation: delete `src/mcp_coder/formatters/` (6 files) and `tests/formatters/` (9 files), update `.importlinter`, `tach.toml`, `tools/tach_docs.py`, `docs/architecture/architecture.md`, `pyproject.toml`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared: `refactor: delete formatters package and update configs`

### Step 3: Remove formatter helpers from pyproject_config
- [ ] Implementation: remove `get_formatter_config()` and `check_line_length_conflicts()` from `pyproject_config.py`, remove 2 test classes from `test_pyproject_config.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared: `refactor: remove formatter helpers from pyproject_config`

## Pull Request

- [ ] PR review: verify all steps complete, grep confirms zero `mcp_coder.formatters` references
- [ ] PR summary prepared
