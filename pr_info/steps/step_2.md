# Step 2: Implement Prerequisites Module with Tests

## Objective  
Create the prerequisites validation module that handles git status, branch checking, and project validation with comprehensive unit tests.

## LLM Prompt
```
Implement Step 2 from the summary (pr_info/steps/summary.md): Create prerequisites module with comprehensive tests.

Extract prerequisites logic from workflows/implement.py and create:
- tests/workflows/implement/test_prerequisites.py (test-first approach)
- src/mcp_coder/workflows/implement/prerequisites.py 

Mock all git operations and external dependencies. Follow patterns from existing tests like tests/cli/commands/test_commit.py.

Reference the summary document for architecture and ensure all prerequisite checks are covered.
```

## Implementation Details

### WHERE
- `tests/workflows/implement/test_prerequisites.py` 
- `src/mcp_coder/workflows/implement/prerequisites.py`

### WHAT
**Main functions:**
```python
def check_git_clean(project_dir: Path) -> bool
def check_main_branch(project_dir: Path) -> bool  
def check_prerequisites(project_dir: Path) -> bool
def has_implementation_tasks(project_dir: Path) -> bool
```

### HOW
- Extract logic from original `workflows/implement.py`
- Mock `git_operations` functions in tests
- Use `pytest.fixture` for common test setup
- Follow existing test patterns with `@patch` decorators

### ALGORITHM
```
1. Test-first: Write comprehensive mocked tests
2. Extract prerequisite functions from original script
3. Adapt to use existing utils.git_operations module
4. Handle all error cases with proper logging
5. Validate against test cases
```

### DATA
**Return values:**
- `bool` - success/failure for each check
- Uses existing `Path` objects for directories
- Leverages existing git operation results

## Files Created
- `tests/workflows/implement/test_prerequisites.py`
- `src/mcp_coder/workflows/implement/prerequisites.py`

## Success Criteria
- Critical prerequisite functions tested with mocked dependencies
- 80% test coverage focused on core validation paths
- No real git operations in tests
- Functions integrate with existing git_operations module
