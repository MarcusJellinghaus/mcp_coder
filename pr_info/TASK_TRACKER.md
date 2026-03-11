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

### Step 1: Add Verify Parser to `parsers.py` — [step_1.md](./steps/step_1.md)

- [x] Implement `add_verify_parser()` in `parsers.py` with `--check-models` flag, update `main.py` to use it
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

### Step 2: Refactor Claude CLI Verification to Return Dict — [step_2.md](./steps/step_2.md)

- [x] Move `_get_status_symbols()` to `cli/utils.py` with tests
- [x] Refactor `verify_claude_cli_installation` → `verify_claude()` returning structured dict (no print calls)
- [x] Update `execute_verify()` shim to keep CLI working
- [x] Update all test references from old function name to new
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

### Step 3: Add `verify_langchain()` Domain Function — [step_3.md](./steps/step_3.md)

- [x] Create `verification.py` with `verify_langchain()`, `_mask_api_key()`, `_resolve_api_key()`, `_check_package_installed()`
- [x] Add tests for `verify_langchain()` including config, API key masking, test prompt, and package checks
- [x] Add tests for existing `list_*_models()` functions in `_models.py`
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

### Step 4: Add `verify_mlflow()` Domain Function — [step_4.md](./steps/step_4.md)

- [x] Implement `verify_mlflow()` in `mlflow_logger.py` with URI validation, connectivity, experiment, and artifact checks
- [x] Add tests covering: not installed, disabled, SQLite, HTTP, file://, experiment, artifact location
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

### Step 5: Rewrite `verify.py` as Orchestrator + Formatter — [step_5.md](./steps/step_5.md)

- [x] Implement `execute_verify()` orchestrator calling all 3 domain functions
- [x] Implement `_resolve_active_provider()`, `_format_section()`, `_compute_exit_code()`
- [x] Add orchestration tests and formatting output tests
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

### Step 6: Integration Tests and Final Validation — [step_6.md](./steps/step_6.md)

- [x] Add end-to-end integration tests covering full CLI path
- [x] Add exit code matrix tests (8 scenarios)
- [x] Update existing `test_verify.py` and `test_verify_command.py` for new signatures
- [x] Run full test suite and verify no regressions
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

## Pull Request

- [ ] Review all steps are complete and all checks pass
- [ ] Prepare PR summary covering all changes
