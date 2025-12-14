# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**

1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**

- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Add `_format_toml_error()` Helper Function
[Details](./steps/step_1.md)

- [x] Implement `_format_toml_error()` helper function in `src/mcp_coder/utils/user_config.py`
- [x] Write tests for `_format_toml_error()` in `tests/utils/test_user_config.py`
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 1

### Step 2: Add `load_config()` Function
[Details](./steps/step_2.md)

- [x] Implement `load_config()` function in `src/mcp_coder/utils/user_config.py`
- [x] Write tests for `load_config()` in `tests/utils/test_user_config.py`
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 2

### Step 3: Refactor `get_config_value()` to Use `load_config()`
[Details](./steps/step_3.md)

- [x] Refactor `get_config_value()` to use `load_config()` in `src/mcp_coder/utils/user_config.py`
- [x] Update existing tests to expect `ValueError` on invalid TOML in `tests/utils/test_user_config.py`
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 3

**Commit message:**
```
Step 3: Refactor get_config_value() to use load_config()

Refactored get_config_value() to use load_config() internally instead of
directly using tomllib. This is a behavior change: parse errors now raise
ValueError instead of returning None, making configuration errors explicit.

Changes:
- Replace direct tomllib.load() with load_config() call
- Remove try/except block that silently caught parse errors
- Let ValueError from load_config() propagate to caller
- Update docstring to document the new Raises: ValueError behavior
- Update tests to expect ValueError on invalid TOML and IO errors
```

### Step 4: Update `coordinator.py` to Use `load_config()`
[Details](./steps/step_4.md)

- [ ] Update `execute_coordinator_run()` to use `load_config()` in `src/mcp_coder/cli/commands/coordinator.py`
- [ ] Verify existing tests in `tests/cli/commands/test_coordinator.py` still pass
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 4

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run full test suite and verify all tests pass
- [ ] Run all quality checks (pylint, pytest, mypy) one final time
- [ ] Prepare PR summary with changes overview
