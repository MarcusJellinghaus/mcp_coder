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
executor_test_path = "Windows/Executor/Test"
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

1. **No field renaming**: Keep `executor_test_path` (backward compatible)
2. **No template renaming**: Keep existing Linux templates unchanged
3. **Defaults to Linux**: If `executor_os` not specified, uses Linux templates
4. **Runtime validation**: Windows scripts validate `%VENV_BASE_DIR%` environment variable
5. **Fail-fast validation**: Config validation ensures `executor_os` is valid at load time

### 4. Windows Template Characteristics

**Key Differences from Linux**:
- Use `@echo ON` instead of `set -euo pipefail`
- Use `%WORKSPACE%` and `%VENV_BASE_DIR%` environment variables
- Activate virtual env: `%VENV_BASE_DIR%\.venv\Scripts\activate.bat`
- Use `where` instead of `which`
- Use `if "%VAR%"==""` for validation
- Use `exit /b 1` for error exits
- Use `.mcp.json` (not `.mcp.linux.json`)
- No git commands (Jenkins handles checkout)

## Files to be Created or Modified

### Files to Modify

1. **src/mcp_coder/cli/commands/coordinator.py**
   - Add 4 Windows template constants
   - Update `load_repo_config()` to load `executor_os`
   - Update `validate_repo_config()` to validate `executor_os`
   - Update `execute_coordinator_test()` to select template
   - Update `dispatch_workflow()` to select templates

2. **src/mcp_coder/utils/user_config.py**
   - Update `create_default_config()` template with `executor_os` example

3. **tests/cli/commands/test_coordinator.py**
   - Add tests for `executor_os` validation
   - Add tests for Windows template selection

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
- No breaking changes to existing field names
- All existing Linux functionality preserved

## Validation Rules

1. `executor_os` must be `"windows"` or `"linux"` (case-sensitive)
2. `executor_os` defaults to `"linux"` if not specified
3. `executor_test_path` still required (no change)
4. Windows scripts validate `%VENV_BASE_DIR%` at runtime

## Error Messages

**Invalid executor_os**:
```
Config file: /path/config.toml - section [coordinator.repos.repo_name] - value for field 'executor_os' invalid. Must be 'windows' or 'linux'
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
