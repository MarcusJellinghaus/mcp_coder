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

### Step 1: Create CLI Command Module and Refactor Error Handling
[Details: pr_info/steps/step_1.md](steps/step_1.md)

- [x] Refactor `resolve_project_dir` in `workflows/utils.py` to raise `ValueError` instead of `sys.exit(1)`
- [x] Update `workflows/validate_labels.py` with try/except wrapper for `resolve_project_dir`
- [x] Create CLI command module at `src/mcp_coder/cli/commands/define_labels.py`
- [x] Implement `calculate_label_changes` function
- [x] Implement `apply_labels` function (raises exceptions instead of `sys.exit`)
- [x] Implement `execute_define_labels` function with exception handling
- [x] Run pylint on new/modified files
- [x] Run pytest on related tests
- [x] Run mypy on new/modified files
- [x] Prepare git commit message for Step 1

### Step 2: Integrate Command into CLI
[Details: pr_info/steps/step_2.md](steps/step_2.md)

- [x] Add import for `execute_define_labels` in `main.py`
- [x] Add `define-labels` subparser with `--project-dir` and `--dry-run` options
- [x] Add command routing to call `execute_define_labels(args)`
- [x] Add `define-labels` command to help text in `help.py`
- [x] Run pylint on modified files
- [x] Run pytest on CLI tests
- [x] Run mypy on modified files
- [x] Prepare git commit message for Step 2

### Step 3: Move and Update Tests
[Details: pr_info/steps/step_3.md](steps/step_3.md)

- [x] Create `tests/cli/commands/test_define_labels.py` from old test file
- [x] Update all imports to new module paths
- [x] Update all mock patches to new module paths
- [x] Remove `TestArgumentParsing` class
- [x] Update `TestResolveProjectDir` tests to expect `ValueError` instead of `SystemExit`
- [x] Update `TestApplyLabels` tests to expect `RuntimeError` instead of `SystemExit`
- [x] Add minimal `TestExecuteDefineLabels` class
- [x] Update `tests/workflows/implement/test_core.py` to expect `ValueError`
- [x] Run pylint on test files
- [x] Run pytest on all updated tests
- [x] Run mypy on test files
- [x] Prepare git commit message for Step 3

### Step 4: Update Documentation
[Details: pr_info/steps/step_4.md](steps/step_4.md)

- [x] Create `docs/getting-started/LABEL_SETUP.md` with label configuration docs
- [x] Update `README.md` with Setup section and `define-labels` command
- [x] Update `pr_info/DEVELOPMENT_PROCESS.md` link to new documentation
- [x] Update `docs/configuration/CONFIG.md` link to new documentation
- [x] Verify all internal links work correctly
- [x] Run pylint (if applicable)
- [x] Run pytest (if applicable)
- [x] Run mypy (if applicable)
- [x] Prepare git commit message for Step 4

### Step 5: Remove Old Files and Final Verification
[Details: pr_info/steps/step_5.md](steps/step_5.md)

- [ ] Delete `workflows/define_labels.py`
- [ ] Delete `workflows/define_labels.bat`
- [ ] Delete `docs/configuration/LABEL_WORKFLOW_SETUP.md`
- [ ] Delete `tests/workflows/test_define_labels.py`
- [ ] Search for and update any remaining references to deleted files
- [ ] Verify `resolve_project_dir` raises `ValueError` (not `sys.exit`)
- [ ] Verify `apply_labels` raises `RuntimeError` on API errors
- [ ] Run full test suite: `pytest tests/ -m "not github_integration and not git_integration"`
- [ ] Verify CLI commands work: `mcp-coder define-labels --help`, `mcp-coder help`
- [ ] Run pylint on all modified files
- [ ] Run mypy on all modified files
- [ ] Prepare git commit message for Step 5

---

## Pull Request

- [ ] Review all changes for consistency and completeness
- [ ] Verify all acceptance criteria are met
- [ ] Prepare PR summary with overview of changes
- [ ] Create pull request
