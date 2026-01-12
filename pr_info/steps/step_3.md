# Step 3: Fix Dead Code in Test Files

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Clean up unused imports and variables in test files identified by Vulture.
These are high-confidence (90-100%) findings in test code.
```

## WHERE
| File | Action |
|------|--------|
| `tests/llm/providers/test_provider_structure.py` | Remove unused imports |
| `tests/test_mcp_code_checker_integration.py` | Remove unused import |
| `tests/workflows/create_pr/test_file_operations.py` | Remove unused variable |
| `tests/workflows/test_create_pr_integration.py` | Remove unused import |
| `tests/integration/test_execution_dir_integration.py` | Fix unused fixture variables |

## WHAT

### 1. test_provider_structure.py (line 34)
**Remove unused imports:**
```python
# Remove these if unused:
claude_cli_verification
claude_executable_finder
```

### 2. test_mcp_code_checker_integration.py (line 12)
**Remove unused import:**
```python
# Remove:
from mcp_coder.mcp_code_checker import has_mypy_errors
```

### 3. test_file_operations.py (line 301)
**Remove unused variable:**
```python
# Find and remove or use:
mock_read_text  # 100% confidence unused
```

### 4. test_create_pr_integration.py (line 25)
**Remove unused import:**
```python
# Remove:
git_repo_with_files  # fixture import not used
```

### 5. test_execution_dir_integration.py (lines 214, 269, 328, 381, 453, 506, 549)
**Fix unused fixture variables:**
```python
# Pattern - change from:
def test_something(require_claude_cli, other_fixture):
    # require_claude_cli not used in body

# To (prefix with underscore to indicate intentional non-use):
def test_something(_require_claude_cli, other_fixture):
    # Fixture triggers skip logic but value not needed
```

## HOW
1. Read each file
2. Identify the unused import/variable
3. Either remove it or prefix with `_` if it's a fixture needed for side effects
4. Run tests to verify no regressions

## ALGORITHM
```
For each file:
1. Read current content
2. Locate unused import/variable at specified line
3. If import: remove the line
4. If fixture param: rename to _param_name
5. If variable: remove assignment or use it
6. Run file's tests to verify
```

## VERIFICATION
```bash
# Run affected test files:
pytest tests/llm/providers/test_provider_structure.py -v
pytest tests/test_mcp_code_checker_integration.py -v
pytest tests/workflows/create_pr/test_file_operations.py -v
pytest tests/workflows/test_create_pr_integration.py -v
pytest tests/integration/test_execution_dir_integration.py -v

# Verify vulture finds no new issues:
vulture tests --min-confidence 90
```

## DATA
No data structures changed - this is purely cleanup of unused code in tests.
