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
- [x] Apply redaction to `serializable_params` before logging
- [x] Apply redaction to `result_for_log` before logging
- [x] Write tests first (TDD)
- [x] Run quality checks (pylint, pytest, mypy) and fix issues
- [x] Prepare git commit message for Step 1

**Commit message for Step 1:**
```
feat(log_utils): add sensitive field redaction to log_function_call decorator

Add optional `sensitive_fields` parameter to the `@log_function_call` decorator
that redacts sensitive values (tokens, API keys, passwords) before logging.

Changes:
- Add `_redact_for_logging()` helper function for recursive dict redaction
- Modify `log_function_call` decorator to accept `sensitive_fields` parameter
- Apply redaction to function parameters and return values before logging
- Original function parameters and return values remain unchanged
- Decorator remains backward compatible - works with or without parentheses

Usage:
  @log_function_call(sensitive_fields=["token", "api_token"])
  def load_config() -> dict:
      return {"token": "secret", "user": "admin"}
  # Logs: {"token": "***", "user": "admin"}

Addresses Issue #228 security vulnerability where secrets were logged in plaintext.
```

---

### Step 2: Fix Logger Name to Use Decorated Function's Module
> See: [pr_info/steps/step_2.md](steps/step_2.md)

- [x] Write tests first (TDD)
- [x] Create `func_logger = logging.getLogger(func.__module__)` inside wrapper
- [x] Replace `stdlogger.debug(...)` → `func_logger.debug(...)`
- [x] Replace `stdlogger.error(...)` → `func_logger.error(...)`
- [x] Update structlog call: `structlog.get_logger(module_name)` uses same module
- [x] Keep `stdlogger` for `setup_logging()` internal logs
- [x] Run quality checks (pylint, pytest, mypy) and fix issues
- [x] Prepare git commit message for Step 2

**Commit message for Step 2:**
```
fix(log_utils): use decorated function's module for logger name

Fix the `@log_function_call` decorator to use the decorated function's module
name for the logger instead of the log_utils module name.

Changes:
- Create `func_logger = logging.getLogger(func.__module__)` inside wrapper
- Replace `stdlogger.debug()` with `func_logger.debug()` for function logs
- Replace `stdlogger.error()` with `func_logger.error()` for error logs
- Keep `stdlogger` for `setup_logging()` internal initialization logs
- structlog already uses `module_name` (func.__module__) correctly

Before:
  2026-01-02 21:32:15 - mcp_coder.utils.log_utils - DEBUG - load_config completed...

After:
  2026-01-02 21:32:15 - mcp_coder.utils.user_config - DEBUG - load_config completed...

This makes log output more useful by showing which module the decorated
function belongs to, enabling better filtering and debugging.
```

---

### Step 3: Add Batch `get_config_values()` Function
> See: [pr_info/steps/step_3.md](steps/step_3.md)

- [x] Write tests first (TDD)
- [x] Remove `@log_function_call` from `get_config_file_path()`
- [x] Add `@log_function_call(sensitive_fields=["token", "api_token"])` to `load_config()`
- [x] Add helper `_get_nested_value(config_data, section, key)`
- [x] Implement `get_config_values()` function
- [x] Remove `get_config_value()` function
- [x] Run quality checks (pylint, pytest, mypy) and fix issues
- [x] Prepare git commit message for Step 3

**Commit message for Step 3:**
```
feat(user_config): add batch get_config_values() function

Add new `get_config_values()` batch function that retrieves multiple
config values in a single disk read, improving performance for callers
that need multiple configuration values.

Changes:
- Add `get_config_values()` function with lazy config loading
- Add `_get_nested_value()` helper for dot-notation section navigation
- Add `@log_function_call(sensitive_fields=[...])` to `load_config()`
- Remove `@log_function_call` from `get_config_file_path()` (reduces noise)
- Remove deprecated `get_config_value()` function (replaced by batch)
- Update module exports in `__init__.py`
- Add comprehensive tests for new batch function

Usage:
  config = get_config_values([
      ("github", "token", None),
      ("jenkins", "server_url", None),
  ])
  token = config[("github", "token")]

Note: Callers still using get_config_value() will be migrated in Step 4.
Test updates will follow in Step 5.
```

---

### Step 4: Refactor All Callers to Use Batch Config Function
> See: [pr_info/steps/step_4.md](steps/step_4.md)

- [x] Update `base_manager.py` - 1 call site
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
