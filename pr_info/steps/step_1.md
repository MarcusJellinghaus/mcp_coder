# Step 1: Add Git Branch Diff Function with Tests

## WHERE
- **Test File**: `tests/utils/test_git_workflows.py` (add new test class)
- **Implementation**: `src/mcp_coder/utils/git_operations.py`

## WHAT
Add function to generate git diff between current branch and main/master branch.

### Main Function Signature
```python
def get_branch_diff(project_dir: Path, base_branch: Optional[str] = None, exclude_paths: Optional[list[str]] = None) -> str
```

## HOW

### Integration Points
- **Import**: Add to existing git_operations.py (no new module)
- **Dependencies**: Use existing `_safe_repo_context`, `get_default_branch_name`
- **Error Handling**: Follow existing git_operations patterns
- **Testing**: Add to existing test suite structure

### Function Behavior
- Generate diff from base branch to current HEAD
- Auto-detect base branch using existing `get_parent_branch_name()` function
- Exclude specified paths from diff (for filtering planning files)
- Return empty string on error (consistent with existing functions)
- Use same error logging patterns as other git functions

## ALGORITHM (Pseudocode)
```
1. Validate project_dir is git repository
2. Determine base_branch (provided or use get_parent_branch_name())
3. Get current branch name for validation
4. Validate current branch has commits different from base branch
5. Execute: git diff base_branch...HEAD --unified=5 --no-prefix with exclusions
6. Return diff string or empty on error
```

## LLM Prompt

### Context
You are implementing Step 1 of the Create Pull Request Workflow. Review the summary document in `pr_info/steps/summary.md` for full context.

### Task
Add a `get_branch_diff()` function to `src/mcp_coder/utils/git_operations.py` that generates git diff between branches.

### Requirements
1. **TDD Approach**: Write comprehensive tests first in `tests/utils/test_git_workflows.py`
2. **Follow Existing Patterns**: Study existing functions in git_operations.py for:
   - Error handling with logging
   - Use of `_safe_repo_context` 
   - Repository validation
   - Function documentation style
3. **Test Coverage**: Include tests for:
   - Valid diff generation
   - Invalid repository
   - Missing base branch
   - Empty diff scenarios
   - Path exclusion functionality
   - Branch validation (no commits different from base)
4. **Integration**: Ensure function works with existing git operation utilities

### Expected Output
- Test class with 4-5 test methods
- Function implementation (~20 lines)
- Proper error handling and logging
- Documentation following existing style

### Success Criteria
- All tests pass
- Function integrates cleanly with existing codebase
- Follows established error handling patterns
- Returns properly formatted git diff string