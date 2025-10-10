# Create Plan Workflow - Implementation Summary

## Overview

Implement a new workflow script `create_plan.py` and `create_plan.bat` that automates the generation of implementation plans for GitHub issues. This workflow mirrors the structure of `create_pr.py` but focuses on the planning phase rather than PR finalization.

## Architectural Changes

### New Components

1. **Workflow Scripts**
   - `workflows/create_plan.py` - Main Python workflow orchestration
   - `workflows/create_plan.bat` - Windows batch wrapper for easy execution

2. **Prompt Updates**
   - Add "Plan Generation Workflow" section to `src/mcp_coder/prompts/prompts.md`
   - Update `PR_Info/DEVELOPMENT_PROCESS.md` to reference centralized prompts

### No New Dependencies

This implementation uses only existing utilities and patterns:
- GitHub operations via `IssueManager` and `IssueBranchManager`
- Git operations via existing `utils.git_operations` functions
- LLM interaction via existing `llm.interface` module
- Prompt management via existing `prompt_manager` module

## Design Principles

### Keep It Simple

- Reuse existing patterns from `create_pr.py`
- No new abstractions or frameworks
- Fail-fast error handling (no retries)
- Direct, linear workflow execution

### Consistency

- Follow same structure as `create_pr.py`
- Use same logging conventions
- Use same argument parsing patterns
- Use same validation patterns

## Core Workflow

```
1. Parse arguments (issue_number, project_dir, log_level, llm_method)
2. Setup logging
3. Validate prerequisites (clean repo, issue exists)
4. Manage branch (create or use existing linked branch)
5. Verify pr_info/steps/ is empty
6. Run three prompts with session continuation
7. Validate output files exist
8. Commit and push
```

## Files to Create or Modify

### New Files
- `workflows/create_plan.py` (main implementation, ~400-500 lines)
- `workflows/create_plan.bat` (batch wrapper, ~30 lines)

### Modified Files
- `src/mcp_coder/prompts/prompts.md` (add Plan Generation Workflow section)
- `PR_Info/DEVELOPMENT_PROCESS.md` (replace inline prompts with links)

## Key Functions

The workflow will implement these main functions:

1. `parse_arguments()` - Parse CLI arguments
2. `resolve_project_dir()` - Validate and resolve project directory
3. `check_prerequisites()` - Validate repo state and issue
4. `manage_branch()` - Get or create linked branch
5. `verify_steps_directory()` - Ensure pr_info/steps/ is empty
6. `run_planning_prompts()` - Execute three prompts with session continuation
7. `validate_output_files()` - Check required files exist
8. `main()` - Orchestrate entire workflow

## Integration Points

- Uses `IssueManager` from `utils.github_operations`
- Uses `IssueBranchManager` from `utils.github_operations`
- Uses `prompt_llm()` from `llm.interface`
- Uses `get_prompt()` from `prompt_manager`
- Uses git operations from `utils.git_operations`
- Uses `setup_logging()` from `utils.log_utils`

## Testing Strategy

Tests will be created in `tests/workflows/create_plan/`:
- `test_argument_parsing.py` - CLI argument validation
- `test_prerequisites.py` - Prerequisite validation logic
- `test_branch_management.py` - Branch creation/selection
- `test_prompt_execution.py` - LLM prompt execution flow
- `test_main.py` - End-to-end workflow with mocks

## Implementation Steps

This implementation is divided into 5 focused steps:

1. **Setup and Argument Parsing** - Create batch wrapper and implement CLI argument parsing
2. **Prerequisites Validation** - Implement repository and issue validation
3. **Branch Management and Directory Verification** - Implement branch operations and directory checks
4. **Prompt Execution and Session Management** - Implement LLM prompt workflow
5. **Finalization and Prompt File Updates** - Implement commit/push and update prompt files

Each step is self-contained and can be implemented and tested independently.
