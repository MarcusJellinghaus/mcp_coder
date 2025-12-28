# Step 0: Refactor Branch Validation

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

Before starting the main implementation, refactor branch validation:
1. Extract the inline validation from create_branch() into a reusable validate_branch_name() function
2. Add unit tests for the new function
3. Update create_branch() to use the new function

This prepares for Step 1 where CIResultsManager will also need branch validation.
```

## WHERE: File Locations
```
src/mcp_coder/utils/git_operations/branches.py    # Extract function
tests/utils/git_operations/test_branches.py       # Add tests
```

## WHAT: Main Components

### New Function
```python
def validate_branch_name(branch_name: str) -> bool:
    """Validate branch name against git naming rules.
    
    Args:
        branch_name: Branch name to validate
        
    Returns:
        True if valid, False otherwise
        
    Validation rules:
        - Must be non-empty string
        - Cannot contain: ~ ^ : ? * [
    """
```

### Current Inline Code to Extract
From `create_branch()`:
```python
# Basic branch name validation (GitHub-compatible)
invalid_chars = ["~", "^", ":", "?", "*", "["]
if any(char in branch_name for char in invalid_chars):
    logger.error(
        "Invalid branch name: '%s'. Contains invalid characters", branch_name
    )
    return False
```

## HOW: Integration Points

### Update create_branch()
```python
def create_branch(repo_path: Path, branch_name: str, ...) -> bool:
    # Replace inline validation with:
    if not validate_branch_name(branch_name):
        return False
    # ... rest of function
```

### Export from Module
Update `src/mcp_coder/utils/git_operations/__init__.py` to export `validate_branch_name`.

## DATA: Test Cases

### Test Cases Structure
```python
class TestValidateBranchName:
    def test_valid_simple_name(self):
        assert validate_branch_name("main") == True
        
    def test_valid_with_slash(self):
        assert validate_branch_name("feature/xyz") == True
        
    def test_valid_with_numbers(self):
        assert validate_branch_name("123-fix-bug") == True
        
    def test_invalid_empty(self):
        assert validate_branch_name("") == False
        
    def test_invalid_with_tilde(self):
        assert validate_branch_name("branch~1") == False
        
    def test_invalid_with_caret(self):
        assert validate_branch_name("branch^2") == False
        
    def test_invalid_with_colon(self):
        assert validate_branch_name("branch:name") == False
        
    def test_invalid_with_question(self):
        assert validate_branch_name("branch?") == False
        
    def test_invalid_with_asterisk(self):
        assert validate_branch_name("branch*") == False
        
    def test_invalid_with_bracket(self):
        assert validate_branch_name("branch[1]") == False
```

## Success Criteria
- [ ] `validate_branch_name()` function extracted and working
- [ ] Unit tests cover valid and invalid cases
- [ ] `create_branch()` updated to use new function
- [ ] Function exported from module
- [ ] All existing tests still pass
