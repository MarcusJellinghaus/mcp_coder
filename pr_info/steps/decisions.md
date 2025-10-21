# Design Decisions

## Introduction

This document records the key architectural and implementation decisions made during the migration of `create_plan` workflow to a CLI command. 

**Core Principle:** All decisions prioritize preserving existing functionality while improving code organization and user experience. The workflow logic remains 100% identical - only the interface for accessing it changes from a standalone script to a CLI command.

---

## Decision 1: Two-File Architecture (KISS Principle)

**Decision:** Use 2 files (CLI handler + workflow module) instead of 6+ modular files.

**Rationale:**
- The workflow is a linear process that doesn't benefit from excessive modularization
- Keeping related code together improves readability and maintainability
- Follows KISS (Keep It Simple, Stupid) principle
- Reduces cognitive overhead for future developers

**Files:**
- `src/mcp_coder/cli/commands/create_plan.py` (~40 lines) - Thin CLI handler
- `src/mcp_coder/workflows/create_plan.py` (~450 lines) - Complete workflow logic

**Alternative Rejected:** Breaking workflow into 6+ modules (prerequisites, branch_mgmt, prompts, validation, etc.) would add unnecessary complexity for a straightforward linear workflow.

---

## Decision 2: Return Exit Codes Instead of sys.exit()

**Decision:** Refactor `main()` to `run_create_plan_workflow()` that returns exit codes instead of calling `sys.exit()`.

**Rationale:**
- Separation of concerns: CLI layer handles exit codes, workflow layer returns them
- Better testability: Can test workflow return values without process termination
- Enables workflow reuse in different contexts (API, other tools)
- Follows established pattern from `implement` command

**Change:**
```python
# Before (standalone script)
def main() -> None:
    # ... workflow logic ...
    sys.exit(0)  # or sys.exit(1)

# After (workflow module)
def run_create_plan_workflow(...) -> int:
    # ... workflow logic ...
    return 0  # or return 1
```

---

## Decision 3: Lazy Import in CLI Handler

**Decision:** Use lazy import for `run_create_plan_workflow` inside `execute_create_plan()` function.

**Rationale:**
- Avoids potential circular dependency issues during module initialization
- Workflow module might have heavy imports that delay CLI startup
- Defensive programming - only load workflow code when command is actually used
- Follows existing pattern in other CLI commands

**Implementation:**
```python
def execute_create_plan(args: argparse.Namespace) -> int:
    # ... setup code ...
    
    # Lazy import to avoid circular dependency
    from ...workflows.create_plan import run_create_plan_workflow
    
    return run_create_plan_workflow(...)
```

---

## Decision 4: Keep resolve_project_dir() in Workflow Module

**Decision:** Keep `resolve_project_dir()` function in the workflow module for backward compatibility.

**Rationale:**
- Although CLI layer now handles project directory resolution, the workflow module may be called directly in other contexts
- Preserves backward compatibility if other code directly imports the workflow module
- Minimal code (~20 lines) so no maintenance burden
- Defensive programming - workflow can validate inputs independently

**Note:** This function is called by CLI but also available for direct workflow usage.

---

## Decision 5: Move CLI Argument Parsing Tests to CLI Test Suite

**Decision:** Delete `TestParseArguments` class from `tests/workflows/create_plan/test_argument_parsing.py` and create new tests in `tests/cli/commands/test_create_plan.py`.

**Rationale:**
- Separation of concerns: CLI tests belong with CLI code, workflow tests with workflow code
- Avoids testing implementation details that no longer exist in the workflow module
- CLI tests use proper mocking of the workflow layer
- Workflow tests focus on business logic, not argument parsing

**Changes:**
- Remove: `TestParseArguments` from workflow tests (~4 tests)
- Add: CLI handler tests in `tests/cli/commands/test_create_plan.py` (2 minimal tests)
- Keep: `TestResolveProjectDir` in workflow tests (utility function tests)

---

## Decision 6: No Functional Changes to Workflow Logic

**Decision:** Preserve 100% of existing workflow functionality - only change the interface for accessing it.

**Rationale:**
- Migration is about code organization and user experience, not behavior changes
- Reduces risk of introducing bugs
- Easier to verify correctness through testing
- Users get same functionality with better interface

**What Changes:**
- ✅ Interface: `python workflows/create_plan.py 123` → `mcp-coder create-plan 123`
- ✅ Module location: `workflows/` → `src/mcp_coder/workflows/`
- ✅ Function signature: `main()` → `run_create_plan_workflow(issue_number, project_dir, provider, method)`

**What Stays Identical:**
- ✅ All workflow steps (prerequisites, branch management, prompts, validation, commit, push)
- ✅ All validation logic
- ✅ All git operations
- ✅ All LLM interactions
- ✅ All error handling within workflow
- ✅ All output files and formats

**Verification:** All existing workflow tests pass with only import path updates - no logic changes needed.

---

## Summary

These decisions create a migration that:
1. **Improves** code organization (proper package structure)
2. **Improves** user experience (consistent CLI interface)
3. **Preserves** all existing functionality (no behavior changes)
4. **Reduces** complexity (KISS principle applied)
5. **Maintains** testability (separation of concerns)
6. **Follows** established patterns (consistency with other commands)

The result is a cleaner, more maintainable codebase with no functional regressions.
