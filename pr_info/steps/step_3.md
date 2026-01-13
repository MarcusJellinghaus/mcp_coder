# Step 3: Clean Up Test Files

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Remove unused imports and variables in test files identified by Vulture.
These are high-confidence (90-100%) findings that should be removed.

Note: Some items are whitelisted (pytest fixtures, import tests) - do NOT modify those.
```

## WHERE
| File | Action |
|------|--------|
| `tests/test_mcp_code_checker_integration.py` | Remove unused import |
| `tests/workflows/create_pr/test_file_operations.py` | Rename unused mock parameter |
| `tests/workflows/test_create_pr_integration.py` | Remove unused import |
| `tests/llm/providers/test_provider_structure.py` | Delete redundant test function |


## WHAT

### 1. test_mcp_code_checker_integration.py (line 12)
**Remove unused import:**
```python
# Current:
from mcp_coder.mcp_code_checker import has_mypy_errors, run_mypy_check

# Change to:
from mcp_coder.mcp_code_checker import run_mypy_check
```

The test `test_has_mypy_errors_convenience_function` doesn't actually use `has_mypy_errors` - it uses `run_mypy_check` and checks the result manually.

### 2. test_file_operations.py (line 301)
**Rename unused mock parameter to indicate intentional non-use:**
```python
# Current:
@patch("pathlib.Path.read_text", side_effect=PermissionError("Access denied"))
@patch("mcp_coder.workflows.create_pr.core.logger")
def test_truncate_with_permission_error(
    self, mock_logger: MagicMock, mock_read_text: MagicMock
) -> None:

# Change to:
@patch("pathlib.Path.read_text", side_effect=PermissionError("Access denied"))
@patch("mcp_coder.workflows.create_pr.core.logger")
def test_truncate_with_permission_error(
    self, mock_logger: MagicMock, _mock_read_text: MagicMock
) -> None:
```

The underscore prefix is standard Python convention for "intentionally unused".

### 3. test_create_pr_integration.py (line 25)
**Remove unused import:**
```python
# Current:
from tests.utils.conftest import git_repo, git_repo_with_files

# Change to:
from tests.utils.conftest import git_repo
```

### 4. test_detection.py - Remove entire file
Since we're removing 5 functions from `detection.py` in Step 2, the tests for those functions should also be removed.

**File to delete:** `tests/utils/test_detection.py`

### 5. test_provider_structure.py - Delete redundant test function
**Delete the entire `test_provider_modules_exist` function:**

This test only verifies that modules are importable, but `test_claude_provider_functions()` already imports and uses these modules. If imports fail, that test would fail anyway - making `test_provider_modules_exist` redundant.

```python
# DELETE this entire function (lines ~30-40):
def test_provider_modules_exist() -> None:
    """Test that all expected provider modules exist and are importable."""
    try:
        from mcp_coder.llm.providers.claude import (
            claude_cli_verification,
            claude_code_api,
            claude_code_cli,
            claude_code_interface,
            claude_executable_finder,
        )
    except ImportError as e:
        pytest.fail(f"Failed to import claude provider modules: {e}")
```

## NOT MODIFIED (Whitelisted)

These items are whitelisted and should NOT be changed:

| File | Item | Reason |
|------|------|--------|
| `tests/integration/test_execution_dir_integration.py` | `require_claude_cli` fixture | Pytest fixture pattern - triggers skip logic |

## ALGORITHM
```
1. Remove unused import from test_mcp_code_checker_integration.py
2. Rename unused parameter in test_file_operations.py to _mock_read_text
3. Remove unused import from test_create_pr_integration.py
4. Delete test_provider_modules_exist function from test_provider_structure.py
5. Run all affected tests to verify no regressions
```

## VERIFICATION
```bash
# Run affected test files:
pytest tests/test_mcp_code_checker_integration.py -v
pytest tests/workflows/create_pr/test_file_operations.py -v
pytest tests/workflows/test_create_pr_integration.py -v
pytest tests/llm/providers/test_provider_structure.py -v

# Verify vulture finds no issues in tests:
vulture tests vulture_whitelist.py --min-confidence 80
```

## DATA
Items being changed:
- 2 unused imports removed
- 1 unused parameter renamed to `_mock_read_text`
- 1 redundant test function deleted
