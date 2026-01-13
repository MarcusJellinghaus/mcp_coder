# Step 2: Remove Dead Code and Apply Fixes in Source Files

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Remove dead code from source files and apply fixes for unused variables.
This includes removing unused imports, functions, methods, and dataclass fields.
Also fix code where variables are defined but not used properly.

Run code quality checks after each file modification.
```

## WHERE
| File | Action |
|------|--------|
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Remove unused import |
| `src/mcp_coder/utils/detection.py` | Delete entire file |
| `src/mcp_coder/utils/data_files.py` | Remove 2 functions + fix variable |
| `src/mcp_coder/utils/jenkins_operations/client.py` | Remove 2 items |
| `tests/utils/test_detection.py` | Delete entire file |
| `src/mcp_coder/workflows/implement/task_processing.py` | Fix: use CONVERSATIONS_DIR constant |

## WHAT

### 1. pr_manager.py - Remove unused import (line 12)
```python
# REMOVE this line:
from github.PullRequest import PullRequest
```

### 2. detection.py - Delete entire module
Delete the entire file. All 8 functions are unused:
- `_detect_active_venv`, `find_virtual_environments`, `get_venv_python`, `get_python_info`, `get_project_dependencies` - no external callers
- `is_valid_venv`, `is_valid_conda_env`, `validate_python_executable` - only called by the above functions

Also delete the test file: `tests/utils/test_detection.py`

### 3. data_files.py - Remove 2 functions + fix variable

**Remove functions:**
- `find_package_data_files` (line 593) - wrapper function, never called
- `get_package_directory` (line 632) - utility function, never called

**Fix variable (line 259):**
```python
# Current (variable assigned but not used):
module_file_absolute = str(Path(package_module.__file__).resolve())
logger.debug(
    "METHOD 3/5: Module __file__ found",
    extra={"method": "module_file", "module_file": package_module.__file__},
)

# Fix option 1 - Use the variable in logger:
module_file_absolute = str(Path(package_module.__file__).resolve())
logger.debug(
    "METHOD 3/5: Module __file__ found",
    extra={"method": "module_file", "module_file": module_file_absolute},
)

# Fix option 2 - Remove the variable entirely (simpler):
logger.debug(
    "METHOD 3/5: Module __file__ found",
    extra={"method": "module_file", "module_file": package_module.__file__},
)
```
Choose option 2 (remove variable) for simplicity.

### 4. jenkins/client.py - Remove 2 items

**Remove function (line 52):**
- `_get_jenkins_config` - config loader that was never integrated

**Remove method (line 251):**
- `get_queue_summary` - queue monitoring method, never called

### 5. task_processing.py - Fix: use CONVERSATIONS_DIR constant

The constant `CONVERSATIONS_DIR` is defined but the path is hardcoded elsewhere.

**Find and replace hardcoded paths:**
```python
# Current (hardcoded):
conversations_dir = project_dir / PR_INFO_DIR / ".conversations"

# Fix (use constant):
conversations_dir = project_dir / CONVERSATIONS_DIR
```

**Note:** `CONVERSATIONS_DIR = f"{PR_INFO_DIR}/.conversations"` is a string, so usage should be:
```python
conversations_dir = project_dir / CONVERSATIONS_DIR
```

Apply this fix in:
- `save_conversation` function
- `save_conversation_comprehensive` function

## ALGORITHM
```
For each file:
1. Read the file
2. Make the specified changes
3. Run pylint on the file
4. Run mypy on the file
5. Run relevant tests
6. Proceed to next file
```

## VERIFICATION
```bash
# After all changes, verify:
mcp__code-checker__run_pylint_check()
mcp__code-checker__run_mypy_check()
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"])

# Verify vulture finds fewer issues:
vulture src --min-confidence 60
```

## DATA
Items being removed:
- 1 unused import (PullRequest)
- 1 entire module deleted (detection.py - 8 functions)
- 2 unused functions (data_files.py)
- 1 unused function + 1 unused method (jenkins/client.py)
- 1 test file deleted (test_detection.py)
- 1 unused variable fixed (module_file_absolute)
- 1 constant usage fixed (CONVERSATIONS_DIR)
