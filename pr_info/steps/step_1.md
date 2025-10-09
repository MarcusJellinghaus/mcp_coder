# Step 1: Branch Name Sanitization

## LLM Prompt
```
Read pr_info/steps/summary.md for context.

Implement Step 1: Branch name sanitization utility function with tests.
Create the function and comprehensive unit tests following TDD principles.
Use the existing test patterns from test_issue_manager.py as reference.
```

## WHERE
**File**: `src/mcp_coder/utils/github_operations/issue_branch_manager.py`  
**Test File**: `tests/utils/github_operations/test_issue_branch_manager.py`

## WHAT

### Main Function
```python
def generate_branch_name_from_issue(
    issue_number: int,
    issue_title: str,
    max_length: int = 200
) -> str:
    """Generate sanitized branch name matching GitHub's native rules.
    
    max_length defaults to 200 (conservative limit to handle Unicode safely).
    """
```

### Test Cases (implement first)
```python
class TestBranchNameGeneration:
    def test_basic_sanitization()
    def test_dash_conversion()  # " - " -> "---"
    def test_lowercase()
    def test_alphanumeric_only()
    def test_spaces_to_dashes()
    def test_strip_leading_trailing_dashes()
    def test_truncation_preserves_issue_number()
    def test_empty_title()
    def test_special_characters()
    def test_multiple_spaces()
    def test_unicode_characters()
    def test_emoji_handling()
```

## HOW

### Integration Points
- Standalone utility function (no class yet)
- No external dependencies beyond Python stdlib
- Will be imported by `IssueBranchManager` in later steps

### Imports Needed
```python
import re
```

## ALGORITHM

### Core Logic (5-6 lines)
```
1. Replace " - " with "---" (GitHub-specific rule)
2. Convert to lowercase
3. Replace non-alphanumeric (except dash) with dash
4. Replace multiple consecutive dashes with single dash
5. Strip leading/trailing dashes
6. Truncate to max_length characters: f"{issue_number}-{truncated_title}" if needed
```

## DATA

### Input Parameters
- `issue_number: int` - Issue number (e.g., 123)
- `issue_title: str` - Raw issue title (e.g., "Add New Feature - Part 1")
- `max_length: int` - Max branch name length in characters (default 200)

### Return Value
- `str` - Sanitized branch name (e.g., "123-add-new-feature---part-1")

### Example Transformations
```python
# Input:  (123, "Add New Feature - Part 1")
# Output: "123-add-new-feature---part-1"

# Input:  (456, "Fix Bug!!!  Multiple   Spaces")
# Output: "456-fix-bug-multiple-spaces"

# Input:  (789, "A" * 300)  # Very long title
# Output: "789-aaaa..." (truncated to 200 characters)
```

## Test-First Implementation Order

1. **Write tests** (test_issue_branch_manager.py):
   - Create test class `TestBranchNameGeneration`
   - Implement all test cases listed above
   - Tests should fail initially

2. **Implement function** (issue_branch_manager.py):
   - Create module with function
   - Implement sanitization logic
   - Run tests until all pass

3. **Verify**:
   - All tests pass
   - Edge cases handled correctly
   - Code is clean and documented
