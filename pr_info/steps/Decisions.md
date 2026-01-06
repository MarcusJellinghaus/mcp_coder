# Code Review Decisions

This document records decisions made during the code review of the coordinator module refactoring.

## Review Date
2026-01-06

## Context
After completing Steps 1-5 of the coordinator refactoring (splitting `coordinator.py` into a package), a code review identified several issues that required decisions.

---

## Decision 1: Duplicate Command Templates

**Issue**: Workflow command templates were defined in both `commands.py` AND `core.py`, creating duplicate code that could diverge.

**Options Considered**:
- A: Keep templates only in `core.py`
- B: Keep templates only in `commands.py`, import into `core.py`
- C: Create a new `constants.py` module for all templates

**Decision**: **Option C** - Create a dedicated module for templates

**Rationale**: Single source of truth, both modules import from the same location, cleaner separation of concerns.

---

## Decision 2: pyproject.toml mypy Change

**Issue**: The PR added `disable_error_code = ["import-untyped"]` globally to mypy configuration.

**Options Considered**:
- A: Keep as-is (global disable)
- B: Move to `[[tool.mypy.overrides]]` for specific modules
- C: Remove the change entirely

**Decision**: **Option C** - Remove the change

**Rationale**: Deal with untyped import warnings individually rather than suppressing them globally.

---

## Decision 3: Documentation Files (pr_info/)

**Issue**: Some step documentation files had mixed/corrupted content and Unicode rendering issues.

**Decision**: **Ignore** - Files in `pr_info/` folder are working documents and don't need cleanup.

---

## Decision 4: WORKFLOW_MAPPING Location

**Issue**: `WORKFLOW_MAPPING` is configuration data that could be separated from business logic.

**Options Considered**:
- A: Move to new constants module (alongside templates)
- B: Keep in `core.py`
- C: Move to dedicated config file (YAML/JSON)

**Decision**: **Option A variant** - Create separate `workflow_constants.py` module

**Rationale**: Keep templates and workflow mapping in separate, focused files for clarity.

---

## Decision 5: Constants Module Naming

**Issue**: Need descriptive names for the new constants modules.

**Options Considered**:
- A: `command_templates.py` + `workflow_constants.py`
- B: `commands_constants.py` + `workflow_mapping_constants.py`
- C: `templates.py` + `workflow_mapping.py`

**Decision**: **Option A** - `command_templates.py` and `workflow_constants.py`

**Rationale**: Clear, descriptive names that indicate content without being overly verbose.

---

## Decision 6: Test File Structure

**Issue**: Test file `test_coordinator.py` is 1,848 lines with 15 test classes.

**Options Considered**:
- A: Symmetrical split matching module structure (test package)
- B: Functional split by feature area
- C: Minimal split (just 2 files)

**Decision**: **Option A** - Symmetrical test structure

**Final Structure**:
```
tests/cli/commands/coordinator/
├── __init__.py
├── test_core.py          # Tests for core.py
├── test_commands.py      # Tests for commands.py
└── test_integration.py   # Integration tests
```

**Rationale**: Matches source module structure, easier to navigate, clear ownership of tests.

---

## Summary of New Module Structure

After implementing these decisions:

```
src/mcp_coder/cli/commands/coordinator/
├── __init__.py              # Public API exports
├── commands.py              # CLI handlers
├── core.py                  # Business logic
├── command_templates.py     # All command template strings
└── workflow_constants.py    # WORKFLOW_MAPPING dict

tests/cli/commands/coordinator/
├── __init__.py
├── test_core.py
├── test_commands.py
└── test_integration.py
```
