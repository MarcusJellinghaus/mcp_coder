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

### Step 1: Migrate `verify_mcp_servers` to `execute_command` — [step_1.md](./steps/step_1.md)
- [ ] Implementation: update `tests/utils/test_mcp_verification.py` (patch `execute_command`, 30s timeout test, parametrized failure test), migrate `src/mcp_coder/utils/mcp_verification.py`, remove the two `mcp_verification` entries from `.importlinter`
- [ ] Quality checks: lint-imports, pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Remove `tests/install` `_env` bypass; document remaining `subprocess` exceptions — [step_2.md](./steps/step_2.md)
- [ ] Implementation: plain `import subprocess` / `import shutil` in `tests/install/conftest.py`, `test_install_integration.py`, `test_install_phases.py`; add `tests.install.** -> subprocess` and the reason comment block to `.importlinter`
- [ ] Quality checks: lint-imports, pylint, pytest (fast suite + `install_integration`), mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review full branch diff against `main`, address findings
- [ ] PR summary prepared
