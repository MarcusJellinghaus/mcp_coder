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

### Step 1: Create Module Structure and Basic Exports

See details: [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Create coordinator package directory structure
- [x] Create basic module files with placeholder content
- [x] Analyze existing coordinator.py public interface
- [x] Create __init__.py with complete public API re-exports
- [x] Verify package can be imported without errors
- [x] Run quality checks: pylint, pytest, mypy on new structure
- [x] Prepare git commit message for Step 1

### Step 2: Move Core Business Logic to core.py

See details: [pr_info/steps/step_2.md](steps/step_2.md)

- [x] Move configuration management functions to core.py
- [x] Move caching system functions and CacheData class to core.py
- [x] Move issue filtering functions to core.py
- [x] Move workflow dispatch function to core.py
- [x] Update all imports in core.py
- [x] Verify all internal function calls work within core.py
- [x] Run quality checks: pylint, pytest, mypy on core.py
- [x] Prepare git commit message for Step 2

### Step 3: Move CLI Handlers and Templates to commands.py

See details: [pr_info/steps/step_3.md](steps/step_3.md)

- [x] Move CLI entry point functions to commands.py
- [x] Move all command templates and constants to commands.py
- [x] Set up imports from core.py in commands.py
- [x] Verify CLI functions can execute business logic through core imports
- [x] Ensure no circular dependencies between commands.py and core.py
- [x] Run quality checks: pylint, pytest, mypy on commands.py
- [x] Prepare git commit message for Step 3

### Step 4: Update Package Imports and External References

See details: [pr_info/steps/step_4.md](steps/step_4.md)

- [x] Complete coordinator/__init__.py with all public exports
- [x] Update src/mcp_coder/cli/commands/__init__.py for package import
- [x] Update tests/cli/commands/test_coordinator.py imports
- [x] Verify backward compatibility for all existing import patterns
- [x] Test that old import styles still work
- [x] Run quality checks: pylint, pytest, mypy on updated files
- [x] Prepare git commit message for Step 4

### Step 5: Final Verification and Cleanup

See details: [pr_info/steps/step_5.md](steps/step_5.md)

- [x] Run comprehensive test suite for coordinator module
- [x] Verify all import patterns (backward compatible + new specific)
- [x] Test CLI command registration and execution
- [x] Validate no circular dependencies exist
- [x] Remove original coordinator.py file
- [x] Final test run to ensure cleanup didn't break anything
- [x] Run quality checks: pylint, pytest, mypy on final structure
- [x] Prepare git commit message for Step 5

### Step 6: Extract Constants to Dedicated Modules

See details: [pr_info/steps/step_6.md](steps/step_6.md)

- [x] Create `coordinator/command_templates.py` with all template strings
- [x] Create `coordinator/workflow_constants.py` with WORKFLOW_MAPPING
- [x] Update `commands.py` to import from `command_templates.py`
- [ ] Update `core.py` to import from both new modules
- [ ] Remove duplicate templates from `commands.py` and `core.py`
- [ ] Update `__init__.py` exports to use new modules
- [ ] Revert `pyproject.toml` mypy change (remove disable_error_code)
- [ ] Run quality checks: pylint, pytest, mypy
- [ ] Prepare git commit message for Step 6

### Step 7: Restructure Test Files

See details: [pr_info/steps/step_7.md](steps/step_7.md)

- [ ] Create `tests/cli/commands/coordinator/` package with `__init__.py`
- [ ] Create `test_core.py` with core.py test classes
- [ ] Create `test_commands.py` with commands.py test classes
- [ ] Create `test_integration.py` with integration test classes
- [ ] Verify all tests pass in new locations
- [ ] Verify test count matches original (no tests lost)
- [ ] Delete original `tests/cli/commands/test_coordinator.py`
- [ ] Run quality checks: pylint, pytest, mypy
- [ ] Prepare git commit message for Step 7

## Code Review

See details: [pr_info/steps/Decisions.md](steps/Decisions.md)

- [x] Review all implemented changes (Steps 1-5)
- [x] Document code review decisions
- [x] Create additional implementation steps (6-7)

## Pull Request

- [ ] Complete Steps 6-7
- [ ] Run final quality checks on complete implementation
- [ ] Create comprehensive PR summary
- [ ] Verify all acceptance criteria met
