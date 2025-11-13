# Windows Support for Coordinator Commands - Implementation Summary

## Overview

Add Windows batch script support to coordinator commands, enabling execution on Windows Jenkins nodes alongside existing Linux support. Implementation uses a configuration-driven approach with OS selection via `executor_os` field.

## Issue Reference

- **Issue**: #174
- **Title**: coordinator - Create command template for Windows

## Architecture & Design Changes

### 1. Configuration Model Extension

**New Field**: `executor_os`
- **Type**: String (`"windows"` | `"linux"`)
- **Default**: `"linux"` (backward compatible)
- **Location**: `[coordinator.repos.<repo_name>]` section
- **Purpose**: Determines which command templates to use

**Example Configuration**:
```toml
[coordinator.repos.windows_project]
repo_url = "https://github.com/company/windows-app.git"
executor_job_path = "Windows/Executor/Test"  # RENAMED from executor_test_path
executor_os = "windows"  # NEW FIELD
github_credentials_id = "github-pat"
```

### 2. Template Architecture

**Current (Linux only)**:
```
DEFAULT_TEST_COMMAND
CREATE_PLAN_COMMAND_TEMPLATE
IMPLEMENT_COMMAND_TEMPLATE
CREATE_PR_COMMAND_TEMPLATE
```

**New (OS-aware)**:
```
# Existing (Linux)
DEFAULT_TEST_COMMAND
CREATE_PLAN_COMMAND_TEMPLATE
IMPLEMENT_COMMAND_TEMPLATE
CREATE_PR_COMMAND_TEMPLATE

# New (Windows)
DEFAULT_TEST_COMMAND_WINDOWS
CREATE_PLAN_COMMAND_WINDOWS
IMPLEMENT_COMMAND_WINDOWS
CREATE_PR_COMMAND_WINDOWS
```

**Template Selection Logic**:
```python
# Simple conditional based on executor_os
if repo_config["executor_os"] == "windows":
    template = WINDOWS_TEMPLATE
else:
    template = LINUX_TEMPLATE  # default
```

### 3. Key Design Decisions

1. **Field rename**: `executor_test_path` → `executor_job_path` (breaking change, clearer naming)
2. **Jenkins parameter rename**: `EXECUTOR_TEST_PATH` → `EXECUTOR_JOB_PATH` (consistency)
3. **Case-insensitive OS validation**: Accept "Windows"/"Linux" and normalize to lowercase
4. **No template renaming**: Keep existing Linux templates unchanged
5. **Defaults to Linux**: If `executor_os` not specified, uses Linux templates
6. **Runtime validation**: Windows scripts validate `%VENV_BASE_DIR%` environment variable (set by Jenkins pipeline)
7. **Fail-fast validation**: Config validation ensures `executor_os` is valid at load time
8. **MCP config standardization**: Both Windows and Linux use `.mcp.json` (Linux will be updated from `.mcp.linux.json`)
9. **Git operations**: Windows approach (Jenkins handles checkout) is preferred; Linux will be updated later to match

### 4. Windows Template Characteristics

**Key Differences from Linux**:
- Use `@echo ON` instead of `set -euo pipefail`
- Use `%WORKSPACE%` and `%VENV_BASE_DIR%` environment variables
- Activate virtual env: `%VENV_BASE_DIR%\.venv\Scripts\activate.bat`
- Use `where` instead of `which`
- Use `if "%VAR%"==""` for validation
- Use `exit /b 1` for error exits
- Use `.mcp.json` (standardized for both Windows and Linux)
- No git commands (Jenkins handles checkout) - this is the preferred approach

## Files to be Created or Modified

### Files to Modify

1. **src/mcp_coder/cli/commands/coordinator.py**
   - Add 4 Windows template constants
   - Update `load_repo_config()` to load `executor_os` and rename field to `executor_job_path`
   - Update `validate_repo_config()` to validate `executor_os` (case-insensitive) and use `executor_job_path`
   - Update `execute_coordinator_test()` to select template and use `EXECUTOR_JOB_PATH` parameter
   - Update `dispatch_workflow()` to select templates and use `executor_job_path`

2. **src/mcp_coder/utils/user_config.py**
   - Update `create_default_config()` template with `executor_os` and `executor_job_path` (renamed field)

3. **tests/cli/commands/test_coordinator.py**
   - Add tests for `executor_os` validation (including case-insensitivity)
   - Add tests for Windows template selection
   - Update existing tests to use `executor_job_path` instead of `executor_test_path`

### Files to Create

1. **pr_info/steps/summary.md** (this file)
2. **pr_info/steps/step_1.md** - Add Windows template constants
3. **pr_info/steps/step_2.md** - Update config loading and validation
4. **pr_info/steps/step_3.md** - Add template selection logic
5. **pr_info/steps/step_4.md** - Update default config template
6. **pr_info/steps/step_5.md** - Add validation tests

## Implementation Approach

### TDD Workflow

Each step follows Test-Driven Development:
1. Write failing tests for new functionality
2. Implement minimum code to pass tests
3. Refactor if needed
4. Run all quality checks

### Step Sequence

1. **Step 1**: Add Windows template constants (no tests needed - just constants)
2. **Step 2**: Update config loading/validation with tests
3. **Step 3**: Add template selection logic with tests
4. **Step 4**: Update default config template (no tests needed)
5. **Step 5**: Integration validation tests

## Backward Compatibility

- Existing configs without `executor_os` work unchanged (default: `"linux"`)
- **BREAKING CHANGE**: `executor_test_path` renamed to `executor_job_path` - users must update configs
- **BREAKING CHANGE**: Jenkins parameter `EXECUTOR_TEST_PATH` renamed to `EXECUTOR_JOB_PATH`
- All existing Linux functionality preserved

## Validation Rules

1. `executor_os` must be `"windows"` or `"linux"` (case-insensitive, normalized to lowercase)
2. `executor_os` defaults to `"linux"` if not specified
3. `executor_job_path` is required (renamed from `executor_test_path`)
4. Windows scripts validate `%VENV_BASE_DIR%` at runtime (set by Jenkins pipeline)

## Error Messages

**Invalid executor_os**:
```
Config file: /path/config.toml - section [coordinator.repos.repo_name] - value for field 'executor_os' invalid: got 'macos'. Must be 'windows' or 'linux' (case-insensitive)
```

**Runtime error (Windows only)**:
```batch
ERROR: VENV_BASE_DIR environment variable not set
```

## Testing Strategy

- **Unit tests**: Config validation for `executor_os` field
- **Integration tests**: Template selection based on OS
- **Minimal scope**: Only test new functionality, don't modify existing tests
- **Quality gates**: All pylint, pytest, mypy checks must pass

## Benefits

1. **Windows Jenkins support** - Enable coordinator on Windows executors
2. **Explicit configuration** - OS behavior is clear and predictable
3. **Flexible deployment** - Different repos can use different executor types
4. **Backward compatible** - No breaking changes for existing users
5. **Simple implementation** - Minimal code changes, easy to review
