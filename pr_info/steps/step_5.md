# Step 5: Update Existing Workflow Tests

## Objective

Update existing workflow tests to use the new import paths and function names. This ensures all tests continue to pass after the module migration.

## Reference

Review `summary.md` for the list of test files that need updates. The changes are primarily import path updates and function name changes.

## WHERE: File Paths

### Modified Files
- `tests/workflows/create_plan/test_main.py` - Update imports and function references
- `tests/workflows/create_plan/test_argument_parsing.py` - Update imports, remove CLI tests
- `tests/workflows/create_plan/test_prerequisites.py` - Update imports only
- `tests/workflows/create_plan/test_branch_management.py` - Update imports only
- `tests/workflows/create_plan/test_prompt_execution.py` - Update imports only

## WHAT: Changes Required

### 1. Import Path Updates (All Files)
**Before:**
```python
from workflows.create_plan import check_prerequisites, manage_branch, ...
```

**After:**
```python
from mcp_coder.workflows.create_plan import check_prerequisites, manage_branch, ...
```

### 2. Function Name Updates (`test_main.py` only)
**Before:**
```python
from workflows.create_plan import main

with patch("workflows.create_plan.main"):
    main()
```

**After:**
```python
from mcp_coder.workflows.create_plan import run_create_plan_workflow

with patch("mcp_coder.workflows.create_plan.run_create_plan_workflow"):
    run_create_plan_workflow(123, project_dir, "claude", "cli")
```

### 3. Test Cleanup (`test_argument_parsing.py`)
- Remove tests for `parse_arguments()` (now in CLI layer)
- Keep tests for `resolve_project_dir()` (still in workflow module)

## HOW: Integration Points

### File-by-File Changes

#### File 1: `tests/workflows/create_plan/test_main.py`

**Changes:**
1. Update import: `workflows.create_plan` → `mcp_coder.workflows.create_plan`
2. Update function: `main()` → `run_create_plan_workflow()`
3. Update all patch paths: `workflows.create_plan.*` → `mcp_coder.workflows.create_plan.*`
4. Update function calls to pass parameters instead of mocking `parse_arguments()`

**Example patch update:**
```python
# Before
with patch("workflows.create_plan.parse_arguments", return_value=mock_args):
    with patch("workflows.create_plan.resolve_project_dir", return_value=tmp_path):
        with patch("workflows.create_plan.check_prerequisites", return_value=(True, mock_issue_data)):
            main()

# After
with patch("mcp_coder.workflows.create_plan.check_prerequisites", return_value=(True, mock_issue_data)):
    with patch("mcp_coder.workflows.create_plan.manage_branch", return_value="feature-branch"):
        result = run_create_plan_workflow(123, tmp_path, "claude", "cli")
        assert result == 0
```

#### File 2: `tests/workflows/create_plan/test_argument_parsing.py`

**Changes:**
1. Update import path
2. Remove `TestParseArguments` class (CLI argument parsing now tested in `test_cli/commands/test_create_plan.py`)
3. Keep `TestResolveProjectDir` class (workflow utility function)

**Delete this test class:**
```python
class TestParseArguments:
    """Test command line argument parsing."""
    # DELETE THIS ENTIRE CLASS
```

**Keep this test class:**
```python
class TestResolveProjectDir:
    """Test project directory resolution and validation."""
    # KEEP THIS CLASS - just update imports
```

#### File 3: `tests/workflows/create_plan/test_prerequisites.py`

**Changes:**
1. Update import: `workflows.create_plan` → `mcp_coder.workflows.create_plan`
2. Update patch paths in tests

**Simple find/replace:**
- Find: `workflows.create_plan`
- Replace: `mcp_coder.workflows.create_plan`

#### File 4: `tests/workflows/create_plan/test_branch_management.py`

**Changes:**
1. Update import: `workflows.create_plan` → `mcp_coder.workflows.create_plan`
2. Update patch paths in tests

**Simple find/replace:**
- Find: `workflows.create_plan`
- Replace: `mcp_coder.workflows.create_plan`

#### File 5: `tests/workflows/create_plan/test_prompt_execution.py`

**Changes:**
1. Update import: `workflows.create_plan` → `mcp_coder.workflows.create_plan`
2. Update patch paths in tests

**Simple find/replace:**
- Find: `workflows.create_plan`
- Replace: `mcp_coder.workflows.create_plan`

## ALGORITHM: Update Process

**For each test file:**
```python
# 1. Update all import statements
# Replace: from workflows.create_plan import X
# With: from mcp_coder.workflows.create_plan import X

# 2. Update all patch paths (in decorators and context managers)
# Replace: @patch("workflows.create_plan.function_name")
# With: @patch("mcp_coder.workflows.create_plan.function_name")

# 3. For test_main.py only:
# Replace: main() calls
# With: run_create_plan_workflow(issue_number, project_dir, provider, method)

# 4. For test_argument_parsing.py only:
# Delete: TestParseArguments class
# Keep: TestResolveProjectDir class
```

## DATA: Test Structure

### Updated Test Structure
```python
# Old structure (test_main.py)
def test_main_success():
    args = MagicMock(issue_number=123, ...)
    with patch("workflows.create_plan.parse_arguments", return_value=args):
        main()

# New structure (test_main.py)
def test_workflow_success():
    issue_number = 123
    project_dir = Path("/test")
    provider = "claude"
    method = "cli"
    
    with patch("mcp_coder.workflows.create_plan.check_prerequisites", ...):
        result = run_create_plan_workflow(issue_number, project_dir, provider, method)
        assert result == 0
```

## Implementation Details

### Step-by-Step Process

**For `test_main.py`:**
1. Open file
2. Find/replace all `workflows.create_plan` → `mcp_coder.workflows.create_plan`
3. Update function name: `main` → `run_create_plan_workflow`
4. Remove `parse_arguments` mocks
5. Remove `resolve_project_dir` mocks (CLI handles this)
6. Remove `setup_logging` mocks (CLI handles this)
7. Update function calls to pass parameters
8. Update assertions to check return values

**For `test_argument_parsing.py`:**
1. Open file
2. Find/replace all `workflows.create_plan` → `mcp_coder.workflows.create_plan`
3. Delete entire `TestParseArguments` class
4. Keep `TestResolveProjectDir` class unchanged (except import)

**For other test files:**
1. Open file
2. Find/replace all `workflows.create_plan` → `mcp_coder.workflows.create_plan`
3. Save file

## Verification Steps

1. **Run All Workflow Tests:**
   ```bash
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-v", "tests/workflows/create_plan/"]
   )
   ```

2. **Expected Result:**
   All existing tests should pass with updated imports.

3. **Verify Import Changes:**
   ```bash
   # Search for old import pattern - should find 0 results
   grep -r "from workflows.create_plan" tests/workflows/create_plan/
   
   # Search for new import pattern - should find all test files
   grep -r "from mcp_coder.workflows.create_plan" tests/workflows/create_plan/
   ```

4. **Code Quality:**
   ```bash
   mcp__code-checker__run_pylint_check(target_directories=["tests/workflows/create_plan"])
   mcp__code-checker__run_mypy_check(target_directories=["tests/workflows/create_plan"])
   ```

## Test Count Changes

**Before:**
- `test_main.py`: ~10 tests
- `test_argument_parsing.py`: ~8 tests (4 for args, 4 for resolve_project_dir)
- `test_prerequisites.py`: ~6 tests
- `test_branch_management.py`: ~5 tests
- `test_prompt_execution.py`: ~8 tests
- **Total: ~37 tests**

**After:**
- `test_main.py`: ~10 tests (updated)
- `test_argument_parsing.py`: ~4 tests (only resolve_project_dir)
- `test_prerequisites.py`: ~6 tests (updated imports)
- `test_branch_management.py`: ~5 tests (updated imports)
- `test_prompt_execution.py`: ~8 tests (updated imports)
- **Total: ~33 tests**

**Note:** The 4 deleted tests (CLI argument parsing) are replaced by 7 new tests in `tests/cli/commands/test_create_plan.py`, resulting in net +3 tests overall.

## Next Steps

Proceed to **Step 6** to run comprehensive code quality checks on all changes.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md and pr_info/steps/step_5.md.

Implement Step 5: Update Existing Workflow Tests

Requirements:
1. Update all test files in tests/workflows/create_plan/ with new import paths
2. In test_main.py: Update function name from main() to run_create_plan_workflow()
3. In test_main.py: Update function calls to pass parameters instead of mocking parse_arguments()
4. In test_argument_parsing.py: Delete TestParseArguments class, keep TestResolveProjectDir
5. For other test files: Simple find/replace of import paths

File-by-file changes:
- tests/workflows/create_plan/test_main.py (complex changes)
- tests/workflows/create_plan/test_argument_parsing.py (delete class)
- tests/workflows/create_plan/test_prerequisites.py (simple import update)
- tests/workflows/create_plan/test_branch_management.py (simple import update)
- tests/workflows/create_plan/test_prompt_execution.py (simple import update)

After implementation:
1. Run all workflow tests: pytest tests/workflows/create_plan/
2. Verify all tests pass
3. Check that old import pattern is gone: grep -r "from workflows.create_plan" tests/
4. Run pylint and mypy on test files

All tests should continue to pass after these updates.

Do not proceed to the next step yet - wait for confirmation.
```
