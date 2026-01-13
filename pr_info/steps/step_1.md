# Step 1: Remove All Dead Code (Source + Tests)

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Remove all dead code from source and test files identified by Vulture.
This includes deleting entire modules, removing unused imports/functions, and fixing unused variables.
Run code quality checks after completing all changes.
```

## WHERE
| File | Action |
|------|--------|
| `src/mcp_coder/utils/detection.py` | Delete entire file |
| `tests/utils/test_detection.py` | Delete entire file |
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Remove unused import |
| `src/mcp_coder/utils/data_files.py` | Remove 2 functions + fix variable |
| `src/mcp_coder/utils/jenkins_operations/client.py` | Remove 2 items |
| `src/mcp_coder/workflows/implement/task_processing.py` | Fix: use CONVERSATIONS_DIR constant |
| `tests/test_mcp_code_checker_integration.py` | Remove unused import |
| `tests/workflows/create_pr/test_file_operations.py` | Rename unused mock parameter |
| `tests/workflows/test_create_pr_integration.py` | Remove unused import |
| `tests/llm/providers/test_provider_structure.py` | Delete redundant test function |

## WHAT

### 1. Delete entire modules

**Delete `src/mcp_coder/utils/detection.py`:**
All 8 functions are unused. The 5 main functions have no external callers, and the 3 helper functions are only called by those 5.

**Delete `tests/utils/test_detection.py`:**
Tests for the removed module.

### 2. Source file changes

**pr_manager.py - Remove unused import (line 12):**
```python
# REMOVE this line:
from github.PullRequest import PullRequest
```

**data_files.py - Remove 2 functions + fix variable:**

Remove functions:
- `find_package_data_files` (line ~593) - wrapper function, never called
- `get_package_directory` (line ~632) - utility function, never called

Fix unused variable (line ~259) - remove the variable, keep the log:
```python
# Before:
module_file_absolute = str(Path(package_module.__file__).resolve())
logger.debug(
    "METHOD 3/5: Module __file__ found",
    extra={"method": "module_file", "module_file": package_module.__file__},
)

# After (remove unused variable):
logger.debug(
    "METHOD 3/5: Module __file__ found",
    extra={"method": "module_file", "module_file": str(Path(package_module.__file__).resolve())},
)
```

**jenkins/client.py - Remove 2 items:**
- `_get_jenkins_config` function (line ~52) - config loader never integrated
- `get_queue_summary` method (line ~251) - queue monitoring never called

**task_processing.py - Use CONVERSATIONS_DIR constant:**
```python
# Before (hardcoded):
conversations_dir = project_dir / PR_INFO_DIR / ".conversations"

# After (use constant):
conversations_dir = project_dir / CONVERSATIONS_DIR
```
Apply in both `save_conversation` and `save_conversation_comprehensive` functions.

### 3. Test file changes

**test_mcp_code_checker_integration.py (line 12):**
```python
# Before:
from mcp_coder.mcp_code_checker import has_mypy_errors, run_mypy_check

# After:
from mcp_coder.mcp_code_checker import run_mypy_check
```

**test_file_operations.py (line ~301):**
```python
# Before:
def test_truncate_with_permission_error(
    self, mock_logger: MagicMock, mock_read_text: MagicMock
) -> None:

# After (underscore prefix for intentionally unused):
def test_truncate_with_permission_error(
    self, mock_logger: MagicMock, _mock_read_text: MagicMock
) -> None:
```

**test_create_pr_integration.py (line 25):**
```python
# Before:
from tests.utils.conftest import git_repo, git_repo_with_files

# After:
from tests.utils.conftest import git_repo
```

**test_provider_structure.py - Delete entire function:**
Delete `test_provider_modules_exist` function (redundant - other tests already import these modules).

## ALGORITHM
```
1. Delete src/mcp_coder/utils/detection.py
2. Delete tests/utils/test_detection.py
3. Edit pr_manager.py - remove PullRequest import
4. Edit data_files.py - remove 2 functions, fix variable
5. Edit jenkins/client.py - remove 2 items
6. Edit task_processing.py - use CONVERSATIONS_DIR constant
7. Edit test_mcp_code_checker_integration.py - remove import
8. Edit test_file_operations.py - rename parameter
9. Edit test_create_pr_integration.py - remove import
10. Edit test_provider_structure.py - delete function
11. Run all code quality checks
```

## VERIFICATION

After completing all changes:

```python
# Run all code quality checks
mcp__code-checker__run_pylint_check()
mcp__code-checker__run_mypy_check()
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"])

# Run vulture - should only show whitelist-worthy items (API methods, enum values, etc.)
Bash("vulture src tests --min-confidence 80")
```

**Expected vulture output after this step:**
- GitHub API methods (get_issue_events, add_comment, etc.)
- IssueEventType enum values
- Base class attributes (_repo_owner, _repo_name)
- Convenience functions (has_mypy_errors, _retry_with_backoff, has_incomplete_work)
- TypedDict fields, pytest fixtures, argparse patterns
- Dataclass fields (execution_error, runner_type)

These are all items that will be whitelisted in Step 2.

## SUCCESS CRITERIA
- [ ] All tests pass
- [ ] Pylint clean
- [ ] Mypy clean
- [ ] Vulture only shows items intended for whitelist (no genuine dead code)
