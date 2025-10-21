# Summary: Migrate `create_plan` Workflow to CLI Command

## Overview

Convert the standalone `workflows/create_plan.py` script into a proper CLI command `mcp-coder create-plan` following the established CLI pattern. This migration enables consistent user experience, better code organization, and removes dependency on batch file wrappers.

## Goals

- ✅ Unified CLI interface: `mcp-coder create-plan <issue_number> [options]`
- ✅ Consistent pattern with existing commands (e.g., `implement`)
- ✅ Better code organization under `src/mcp_coder/`
- ✅ Eliminate Windows batch file dependency
- ✅ Preserve all existing functionality
- ✅ All tests passing with minimal changes

## Architectural / Design Changes

### Current Architecture
```
workflows/
├── create_plan.py          # Standalone script (485 lines)
└── create_plan.bat         # Windows batch wrapper

Usage: python workflows/create_plan.py <issue_number> [options]
```

**Issues:**
- Standalone script outside `src/` package structure
- Requires batch file wrapper for convenience
- Inconsistent with other CLI commands
- Direct `sys.exit()` calls in workflow logic

### New Architecture (KISS Approach)
```
src/mcp_coder/
├── cli/commands/
│   └── create_plan.py      # CLI command handler (~40 lines)
└── workflows/
    └── create_plan.py      # Workflow module (~450 lines)

Usage: mcp-coder create-plan <issue_number> [options]
```

**Improvements:**
- ✅ Single workflow module (not over-modularized)
- ✅ Thin CLI handler following established pattern
- ✅ Separation of concerns: CLI parsing vs workflow logic
- ✅ Workflow returns exit codes instead of calling `sys.exit()`
- ✅ Proper package structure under `src/`
- ✅ No batch file needed

### Design Principles Applied

**1. KISS Principle**
- Use 2 files instead of 6+ modular files
- Linear workflow doesn't need complex abstractions
- Keep related code together for easy understanding

**2. Consistency**
- Follow pattern from `implement` command
- Reuse existing utilities (`resolve_project_dir`, `parse_llm_method_from_args`)
- Standard CLI argument structure

**3. Separation of Concerns**
- CLI layer: Argument parsing, help text, exit code handling
- Workflow layer: Business logic, validation, LLM interactions

## Files to Create or Modify

### Files to CREATE

1. **`pr_info/steps/decisions.md`**
   - Documents key architectural and design decisions
   - Emphasizes "no functionality changes" principle
   - 6 decisions documented

2. **`src/mcp_coder/cli/commands/create_plan.py`**
   - New CLI command handler
   - ~40 lines
   - Thin wrapper following `implement.py` pattern

3. **`src/mcp_coder/workflows/create_plan.py`**
   - Relocated workflow module (moved from `workflows/`)
   - ~443 lines (after removing CLI code)
   - Refactored to return exit codes

4. **`tests/cli/commands/test_create_plan.py`**
   - New CLI command tests
   - 2 minimal tests (success + error handling)
   - Follow pattern from `test_implement.py`

### Files to MODIFY

5. **`src/mcp_coder/cli/main.py`**
   - Add `create-plan` subparser
   - Register command handler
   - ~20 lines added

6. **`tests/workflows/create_plan/test_main.py`**
   - Update import path: `workflows.create_plan` → `mcp_coder.workflows.create_plan`
   - Update function name: `main()` → `run_create_plan_workflow()`
   - Minimal changes to test logic

7. **`tests/workflows/create_plan/test_argument_parsing.py`**
   - Update imports for `resolve_project_dir`
   - Remove CLI argument parsing tests (now in CLI layer)
   - Keep directory validation tests

8. **`tests/workflows/create_plan/test_prerequisites.py`**
   - Update import path only
   - No logic changes

9. **`tests/workflows/create_plan/test_branch_management.py`**
   - Update import path only
   - No logic changes

10. **`tests/workflows/create_plan/test_prompt_execution.py`**
   - Update import path only
   - No logic changes

### Files to DELETE

11. **`workflows/create_plan.py`**
    - Original standalone script (replaced by src/ version)

12. **`workflows/create_plan.bat`**
    - Batch wrapper (no longer needed)

## Functional Changes

### Command Interface

**Before:**
```bash
python workflows/create_plan.py 123 --project-dir /path --llm-method claude_code_cli
```

**After:**
```bash
mcp-coder create-plan 123 --project-dir /path --llm-method claude_code_cli
```

**Arguments:**
- `issue_number` (positional, required): GitHub issue number
- `--project-dir` (optional): Project directory path (default: current directory)
- `--llm-method` (optional): `claude_code_cli` or `claude_code_api` (default: `claude_code_cli`)
- `--log-level` (optional): DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

### Workflow Steps (Unchanged)

1. Validate prerequisites (clean git repo, issue exists)
2. Manage branch (create or checkout issue branch)
3. Verify `pr_info/steps/` directory is empty
4. Run three planning prompts with session continuation:
   - Initial Analysis (with issue content)
   - Simplification Review
   - Implementation Plan Creation
5. Validate output files exist (`summary.md`, `step_1.md`)
6. Commit changes: `"Initial plan generated for issue #<issue_number>"`
7. Push changes to remote

## Testing Strategy

### Test Coverage Maintained

All existing tests preserved with minimal changes:
- Prerequisites validation tests
- Branch management tests
- Prompt execution tests
- Output validation tests
- Main workflow orchestration tests

### New Tests Added

- CLI command handler tests
- CLI argument parsing tests
- Integration test for end-to-end CLI execution

### Test Organization

```
tests/
├── cli/commands/
│   └── test_create_plan.py          # NEW: CLI handler tests
└── workflows/create_plan/
    ├── test_main.py                  # MODIFIED: Update imports
    ├── test_argument_parsing.py      # MODIFIED: Focus on workflow utils
    ├── test_prerequisites.py         # MODIFIED: Update imports
    ├── test_branch_management.py     # MODIFIED: Update imports
    └── test_prompt_execution.py      # MODIFIED: Update imports
```

## Migration Benefits

1. **User Experience**
   - Consistent CLI across all commands
   - Standard help text: `mcp-coder create-plan --help`
   - No need to remember script paths

2. **Code Quality**
   - Proper package structure
   - Clear separation of concerns
   - Follows established patterns
   - Better testability

3. **Maintainability**
   - Single workflow module (not over-modularized)
   - Easy to find and understand code
   - Consistent with other workflows

4. **Cross-Platform**
   - No Windows-specific batch files
   - Works on all platforms via CLI

## Risk Assessment

**Low Risk Migration:**
- ✅ Mostly code relocation (not rewrite)
- ✅ Existing functions preserved
- ✅ Comprehensive test coverage
- ✅ Clear rollback path (keep old files until verified)

**Potential Issues:**
- Import path changes might affect external code (mitigated by thorough testing)
- `sys.exit()` → return code refactoring (straightforward change)

## Success Criteria

- [ ] Command works: `mcp-coder create-plan <issue_number>`
- [ ] All command-line options functional
- [ ] All existing tests passing
- [ ] New CLI tests added and passing
- [ ] Code quality checks passing (pylint, mypy, pytest)
- [ ] Old files deleted
- [ ] Documentation updated (README, help text)

## Implementation Approach

Follow **Test-Driven Development** where applicable:
1. Write/update tests first
2. Implement functionality to pass tests
3. Refactor for quality
4. Verify all checks pass

Each step is self-contained and can be validated independently before proceeding to the next.

- `test_prerequisites.py`: ~6 tests (updated imports)
- `test_branch_management.py`: ~5 tests (updated imports)
- `test_prompt_execution.py`: ~8 tests (updated imports)
- **New CLI tests:** 2 minimal tests in `tests/cli/commands/test_create_plan.py`
- **Total: ~35 tests**

**Note:** The 4 deleted CLI parsing tests are replaced by 2 minimal CLI handler tests, resulting in net -2 tests overall. This reduction is intentional - the CLI layer is kept minimal since workflow logic is thoroughly tested separately.

## Key Implementation Notes

**Step 2 is broken into 4 sub-steps for easier verification:**
- **Step 2a:** Copy file to new location (preserve as-is)
- **Step 2b:** Refactor main() → run_create_plan_workflow() 
- **Step 2c:** Remove CLI parsing code (parse_arguments, if __name__)
- **Step 2d:** Clean up imports and verify quality

**CLI tests are kept minimal (2 tests):**
- Success case
- Error handling (combines workflow failure, exceptions, keyboard interrupt)

This minimal approach is justified because:
- The CLI handler is a thin wrapper (just ~40 lines)
- Workflow logic has comprehensive test coverage (~33 tests)
- Reduces test maintenance burden

**See `decisions.md` for full rationale of all design choices.**
