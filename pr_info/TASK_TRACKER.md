# MCP Coder Task Tracker

## Overview

This tracks **Feature Implementation** consisting of multiple **Implementation Steps**.

- **Feature**: A complete user-facing capability
- **Implementation Step**: A self-contained unit of work (tests + implementation)

## Status Legend

- [x] = Implementation step complete
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Add Sensitive Field Redaction to `@log_function_call` Decorator
> See: [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Add `_redact_for_logging()` helper function
- [x] Modify `log_function_call` to accept optional `sensitive_fields` parameter
- [ ] Apply redaction to `serializable_params` before logging
- [ ] Apply redaction to `result_for_log` before logging
- [ ] Write tests first (TDD)
- [ ] Run quality checks (pylint, pytest, mypy) and fix issues
- [ ] Prepare git commit message for Step 1

---

### Step 2: Fix Logger Name to Use Decorated Function's Module
> See: [pr_info/steps/step_2.md](steps/step_2.md)

- [ ] Write tests first (TDD)
- [ ] Create `func_logger = logging.getLogger(func.__module__)` inside wrapper
- [ ] Replace `stdlogger.debug(...)` → `func_logger.debug(...)`
- [ ] Replace `stdlogger.error(...)` → `func_logger.error(...)`
- [ ] Update structlog call: `structlog.get_logger(module_name)` uses same module
- [ ] Keep `stdlogger` for `setup_logging()` internal logs
- [ ] Run quality checks (pylint, pytest, mypy) and fix issues
- [ ] Prepare git commit message for Step 2

---

### Step 3: Add Batch `get_config_values()` Function
> See: [pr_info/steps/step_3.md](steps/step_3.md)

- [ ] Write tests first (TDD)
- [ ] Remove `@log_function_call` from `get_config_file_path()`
- [ ] Add `@log_function_call(sensitive_fields=["token", "api_token"])` to `load_config()`
- [ ] Add helper `_get_nested_value(config_data, section, key)`
- [ ] Implement `get_config_values()` function
- [ ] Remove `get_config_value()` function
- [ ] Run quality checks (pylint, pytest, mypy) and fix issues
- [ ] Prepare git commit message for Step 3

---

### Step 4: Refactor All Callers to Use Batch Config Function
> See: [pr_info/steps/step_4.md](steps/step_4.md)

- [ ] Update `base_manager.py` - 1 call site
- [ ] Update `client.py` - 3 calls → 1 batch
- [ ] Update `core.py` load_repo_config() - 4 calls → 1 batch
- [ ] Update `core.py` get_cache_refresh_minutes() - 1 call
- [ ] Update `core.py` get_jenkins_credentials() - 3 calls → 1 batch
- [ ] Update `tests/conftest.py` - 2 calls → 1 batch
- [ ] Update `tests/utils/jenkins_operations/test_integration.py` - 4 calls → 1 batch
- [ ] Verify no references to `get_config_value` remain (grep codebase)
- [ ] Run quality checks (pylint, pytest, mypy) and fix issues
- [ ] Prepare git commit message for Step 4

---

### Step 5: Update Tests and Final Verification
> See: [pr_info/steps/step_5.md](steps/step_5.md)

- [ ] Update `test_user_config.py` - rename class, update all test methods
- [ ] Update `test_user_config_integration.py` - update all references
- [ ] Update imports in both test files
- [ ] Run grep to verify no old references remain
- [ ] Run full test suite
- [ ] Manual verification of log output format
- [ ] Verify all acceptance criteria met
- [ ] Run quality checks (pylint, pytest, mypy) and fix issues
- [ ] Prepare git commit message for Step 5

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify all acceptance criteria from summary.md are met
- [ ] Run final quality checks (pylint, pytest, mypy)
- [ ] Prepare PR summary with changes overview
- [ ] Create pull request
