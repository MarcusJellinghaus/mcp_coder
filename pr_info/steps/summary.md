# Implementation Plan Summary: Convert create_PR Workflow to CLI Command

## Overview
Convert the standalone `create_PR` workflow script into a proper CLI command (`mcp-coder create-pr`) following the established pattern from the `implement` command while maintaining KISS principle.

## Issue Reference
**GitHub Issue:** #139 - Convert create_PR workflow to CLI command

## Architectural Changes

### Current Architecture (Before)
```
workflows/
├── create_PR.py          # Standalone script with main(), own arg parsing, own resolve_project_dir()
└── create_PR.bat         # Windows batch wrapper

tests/workflows/create_pr/
├── test_file_operations.py
├── test_parsing.py
├── test_prerequisites.py
├── test_generation.py
├── test_repository.py
└── test_main.py
```

**Problems:**
- Code duplication: `resolve_project_dir()` duplicated from `workflows/utils.py`
- Inconsistent interface: Not accessible via `mcp-coder` CLI
- Platform-specific batch wrapper required
- Standalone argument parsing instead of using CLI infrastructure

### Target Architecture (After)
```
src/mcp_coder/workflows/create_pr/
├── __init__.py           # Package exports
└── core.py               # All workflow logic (moved from workflows/create_PR.py)

src/mcp_coder/cli/commands/
└── create_pr.py          # CLI command interface (new)

tests/cli/commands/
└── test_create_pr.py     # CLI command tests (new)

tests/workflows/create_pr/
├── test_file_operations.py   # Updated imports
├── test_parsing.py            # Updated imports
├── test_prerequisites.py      # Updated imports
├── test_generation.py         # Updated imports
├── test_repository.py         # Updated imports
└── test_main.py               # Updated imports
```

**Benefits:**
- ✅ Consistent CLI interface: `mcp-coder create-pr [OPTIONS]`
- ✅ Eliminates code duplication (uses shared `resolve_project_dir()`)
- ✅ Cross-platform (no batch wrapper needed)
- ✅ Standard pip-installed entry point
- ✅ Consistent with `implement` command pattern

## Design Principles

### KISS Approach
**Keep It Simple:**
- Move `workflows/create_PR.py` → `src/mcp_coder/workflows/create_pr/core.py` as a **single file**
- Preserve all existing function organization (no splitting into 5 modules)
- Minimal code changes: only remove duplication and update entry point
- Simple test updates: find/replace imports

**Why NOT splitting into modules:**
- Current file is ~500 lines - manageable size
- Functions already well-organized and named
- Splitting would add complexity without clear benefit
- Easy to split later if needed

### Shared Utilities Reused
1. **`workflows.utils.resolve_project_dir()`** - Project directory validation
2. **`cli.utils.parse_llm_method_from_args()`** - LLM method parsing
3. **Standard CLI error handling patterns** - From existing commands

### Integration Pattern
Following the exact pattern from `implement` command:

```python
# CLI Command (create_pr.py)
def execute_create_pr(args: argparse.Namespace) -> int:
    project_dir = resolve_project_dir(args.project_dir)
    provider, method = parse_llm_method_from_args(args.llm_method)
    return run_create_pr_workflow(project_dir, provider, method)

# Workflow Core (core.py)
def run_create_pr_workflow(project_dir: Path, provider: str, method: str) -> int:
    # Orchestrate workflow steps
    # Return 0 for complete success, 1 for error, 2 for partial success
```

## Files to Create

### New Files (3)
1. **`src/mcp_coder/workflows/create_pr/__init__.py`**
   - Purpose: Package initialization, export main function
   - Content: Export `run_create_pr_workflow`

2. **`src/mcp_coder/workflows/create_pr/core.py`**
   - Purpose: Main workflow orchestration and business logic
   - Source: Moved from `workflows/create_PR.py`
   - Changes: Remove `main()`, `parse_arguments()`, `resolve_project_dir()`

3. **`src/mcp_coder/cli/commands/create_pr.py`**
   - Purpose: CLI command interface
   - Pattern: Copy from `implement.py`
   - Function: `execute_create_pr(args)`

## Files to Modify

### Modified Files (9)
1. **`src/mcp_coder/cli/main.py`**
   - Add: Import `execute_create_pr`
   - Add: `create-pr` subcommand to argument parser
   - Add: Route to `execute_create_pr()` in main()

2. **`tests/workflows/create_pr/test_file_operations.py`**
   - Change: `from workflows.create_PR` → `from mcp_coder.workflows.create_pr.core`

3. **`tests/workflows/create_pr/test_parsing.py`**
   - Change: `from workflows.create_PR` → `from mcp_coder.workflows.create_pr.core`

4. **`tests/workflows/create_pr/test_prerequisites.py`**
   - Change: `from workflows.create_PR` → `from mcp_coder.workflows.create_pr.core`

5. **`tests/workflows/create_pr/test_generation.py`**
   - Change: `from workflows.create_PR` → `from mcp_coder.workflows.create_pr.core`

6. **`tests/workflows/create_pr/test_repository.py`**
   - Change: `from workflows.create_PR` → `from mcp_coder.workflows.create_pr.core`

7. **`tests/workflows/create_pr/test_main.py`**
   - Change: `from workflows.create_PR` → `from mcp_coder.workflows.create_pr.core`
   - Change: Mock paths and function references

8. **`tests/workflows/test_create_pr_integration.py`**
   - Change: Update imports to new module structure

9. **`tests/test_create_pr.py`**
   - Change: Update legacy compatibility shim imports

## Files to Delete

### Removed Files (2)
1. **`workflows/create_PR.py`** - Replaced by `src/mcp_coder/workflows/create_pr/core.py`
2. **`workflows/create_PR.bat`** - No longer needed (CLI handles execution)

## Implementation Steps Overview

### Step 1: Create CLI Command Interface
- **File:** `src/mcp_coder/cli/commands/create_pr.py`
- **Tests:** `tests/cli/commands/test_create_pr.py`
- **Approach:** TDD - Write tests first, implement command second
- **Pattern:** Follow `implement.py` exactly

### Step 2: Create Workflow Package and Core Logic
- **Files:** `src/mcp_coder/workflows/create_pr/__init__.py`, `core.py`
- **Tests:** Update existing test imports
- **Approach:** Move and refactor `workflows/create_PR.py`

### Step 3: Integrate with CLI Main
- **File:** `src/mcp_coder/cli/main.py`
- **Tests:** Manual verification with `mcp-coder create-pr --help`
- **Approach:** Add subcommand and routing

### Step 4: Update All Test Imports
- **Files:** All test files under `tests/workflows/create_pr/`
- **Approach:** Find/replace imports, run tests to validate

### Step 5: Remove Legacy Files
- **Files:** `workflows/create_PR.py`, `workflows/create_PR.bat`
- **Validation:** Run full test suite, verify CLI works

## Code Quality Requirements

### All Steps Must:
1. ✅ Pass **pylint** check (no errors)
2. ✅ Pass **pytest** (all tests, including new ones)
3. ✅ Pass **mypy** type checking (strict mode)

### TDD Requirements:
- Write tests BEFORE implementation
- Red → Green → Refactor cycle
- Each step must have passing tests before proceeding

## Success Criteria

- [ ] Command available: `mcp-coder create-pr --help` works
- [ ] Accepts arguments: `--project-dir PATH`, `--llm-method METHOD`
- [ ] All existing tests pass with updated imports
- [ ] New CLI command tests pass
- [ ] No code duplication (`resolve_project_dir` reused)
- [ ] All code quality checks pass (pylint, pytest, mypy)
- [ ] Legacy files removed
- [ ] Consistent with `implement` command pattern

## Risk Assessment

### Low Risk
- ✅ Simple file movement (not complex refactoring)
- ✅ Tests already exist and are comprehensive
- ✅ Clear pattern to follow (`implement` command)
- ✅ No external API changes

### Mitigation
- Run tests after each step
- Keep commits small and atomic
- Easy rollback if issues arise

## Estimated Complexity

- **Lines of code changed:** ~50-100 (mostly imports)
- **New code:** ~50 lines (CLI command interface)
- **Test updates:** Simple find/replace
- **Time estimate:** 1-2 hours for careful implementation

## Dependencies

### Required Before Starting
- ✅ Existing `implement` command working (pattern to follow)
- ✅ Shared utilities available (`workflows.utils`, `cli.utils`)
- ✅ All existing tests passing

### No External Dependencies
- No new packages required
- No API changes needed
- No configuration updates needed
