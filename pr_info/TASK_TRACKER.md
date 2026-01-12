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

### Step 1: Update Console Formatter in log_utils.py
[Detail: pr_info/steps/step_1.md](steps/step_1.md)

- [x] Add test class `TestExtraFieldsFormatter` to `tests/utils/test_log_utils.py`
- [x] Add `STANDARD_LOG_FIELDS` constant to `log_utils.py`
- [x] Add `ExtraFieldsFormatter` class to `log_utils.py`
- [x] Update `setup_logging()` console handler to use `ExtraFieldsFormatter`
- [x] Update module docstring with usage examples
- [x] Run quality checks (pylint, pytest, mypy) and fix any issues
- [x] Prepare git commit message for Step 1

### Step 2: Refactor jenkins_operations/client.py
[Detail: pr_info/steps/step_2.md](steps/step_2.md)

- [ ] Change `import structlog` to `import logging`
- [ ] Change `logger = structlog.get_logger(__name__)` to `logger = logging.getLogger(__name__)`
- [ ] Update the `logger.debug()` call to use `extra={}`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 2

### Step 3: Refactor data_files.py
[Detail: pr_info/steps/step_3.md](steps/step_3.md)

- [ ] Remove `import structlog` line
- [ ] Remove `structured_logger = structlog.get_logger(__name__)` line
- [ ] Convert all `structured_logger.debug()` to `logger.debug()` with `extra={}`
- [ ] Convert all `structured_logger.info()` to `logger.info()` with `extra={}`
- [ ] Convert all `structured_logger.error()` to `logger.error()` with `extra={}`
- [ ] Verify no remaining references to `structured_logger`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 3

### Step 4: Update Tests in test_data_files.py
[Detail: pr_info/steps/step_4.md](steps/step_4.md)

- [ ] Remove `import structlog` from imports
- [ ] Remove `from structlog.testing import LogCapture` from imports
- [ ] Add `import logging` if not present
- [ ] Update `test_data_file_found_logs_debug_not_info` to use caplog
- [ ] Update `test_data_file_logging_with_info_level` to use caplog
- [ ] Update `test_data_file_logging_with_debug_level` to use caplog
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 4

### Step 5: Finalization and Verification
[Detail: pr_info/steps/step_5.md](steps/step_5.md)

- [ ] Remove the two structlog exception lines from `.importlinter`
- [ ] Run import linter verification
- [ ] Verify no structlog imports outside log_utils.py
- [ ] Run full test suite
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 5

---

## Pull Request

- [ ] Review all implementation steps for completeness
- [ ] Ensure all tests pass
- [ ] Ensure all quality checks pass (pylint, pytest, mypy)
- [ ] Prepare PR summary and description
