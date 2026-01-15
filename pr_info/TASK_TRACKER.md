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

### Step 0: Add Vulture Dependency
*Reference: [pr_info/steps/step_0.md](steps/step_0.md)*

- [x] Add `vulture>=2.14` to `pyproject.toml` dev dependencies
- [x] Verify vulture is available (`vulture --version`)
- [x] Prepare git commit message

---

### Step 1: Remove All Dead Code (Source + Tests)
*Reference: [pr_info/steps/step_1.md](steps/step_1.md)*

- [x] Delete `src/mcp_coder/utils/detection.py` (entire module - all 8 functions unused)
- [x] Delete `tests/utils/test_detection.py` (tests for removed module)
- [x] Remove unused `PullRequest` import from `src/mcp_coder/utils/github_operations/pr_manager.py`
- [x] Remove `find_package_data_files` and `get_package_directory` functions from `src/mcp_coder/utils/data_files.py`
- [x] Fix unused `module_file_absolute` variable in `src/mcp_coder/utils/data_files.py`
- [x] Remove `_get_jenkins_config` and `get_queue_summary` from `src/mcp_coder/utils/jenkins_operations/client.py`
- [x] Use `CONVERSATIONS_DIR` constant in `src/mcp_coder/workflows/implement/task_processing.py`
- [x] Remove unused `has_mypy_errors` import from `tests/test_mcp_code_checker_integration.py`
- [x] Rename `mock_read_text` to `_mock_read_text` in `tests/workflows/create_pr/test_file_operations.py`
- [x] Remove unused `git_repo_with_files` import from `tests/workflows/test_create_pr_integration.py`
- [x] Delete redundant `test_provider_modules_exist` function from `tests/llm/providers/test_provider_structure.py`
- [x] Run pylint check and fix any issues
- [x] Run pytest and fix any failures
- [x] Run mypy check and fix any issues
- [x] Prepare git commit message

---

### Step 2: Create Vulture Whitelist
*Reference: [pr_info/steps/step_2.md](steps/step_2.md)*

- [x] Run vulture to confirm only whitelist-worthy items remain
- [x] Create `vulture_whitelist.py` at project root
- [x] Create `tools/vulture_check.bat` script
- [x] Create `tools/vulture_check.sh` script
- [x] Verify whitelist file has valid Python syntax
- [x] Verify `vulture src tests vulture_whitelist.py --min-confidence 60` returns exit code 0
- [x] Run pylint check and fix any issues
- [x] Run pytest and fix any failures
- [x] Run mypy check and fix any issues
- [x] Prepare git commit message

---

### Step 3: Add CI Integration
*Reference: [pr_info/steps/step_3.md](steps/step_3.md)*

- [x] Add vulture check to architecture job matrix in `.github/workflows/ci.yml`
- [x] Verify CI workflow YAML is valid
- [x] Verify local vulture check still passes
- [x] Run pylint check and fix any issues
- [x] Run pytest and fix any failures
- [x] Run mypy check and fix any issues
- [x] Prepare git commit message

---

### Step 4: Update Documentation
*Reference: [pr_info/steps/step_4.md](steps/step_4.md)*

- [x] Add vulture to architectural tools section in `docs/architecture/ARCHITECTURE.md`
- [x] Add Dead Code Detection subsection in `docs/architecture/ARCHITECTURE.md`
- [x] Add Vulture section in `docs/architecture/dependencies/README.md`
- [x] Verify vulture check still clean
- [x] Run pylint check and fix any issues
- [x] Run pytest and fix any failures
- [x] Run mypy check and fix any issues
- [x] Prepare git commit message

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run final full test suite
- [ ] Run all code quality checks (pylint, pytest, mypy, vulture)
- [ ] Prepare PR summary with changes overview
- [ ] Create pull request
