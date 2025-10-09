# Step 2: Create Branch Name Generation Utility

## LLM Prompt
```
Read pr_info/steps/summary.md and this step file. Implement the branch name generation utility following TDD approach:
1. First write unit tests for generate_branch_name_from_issue()
2. Then implement the function with GitHub's exact sanitization rules
Follow KISS principle and existing code conventions.
```

## WHERE
- **Test File**: `tests/utils/github_operations/test_issue_branch_manager.py` (NEW)
- **Implementation File**: `src/mcp_coder/utils/github_operations/issue_branch_manager.py` (NEW)

## WHAT

### Test Class and Functions
```python
class TestBranchNameGeneration:
    def test_basic_branch_name_generation(self) -> None
    def test_sanitize_spaces_to_dashes(self) -> None
    def test_sanitize_dash_space_dash_to_triple_dash(self) -> None
    def test_lowercase_conversion(self) -> None
    def test_remove_special_characters(self) -> None
    def test_strip_leading_trailing_dashes(self) -> None
    def test_length_truncation_preserves_issue_number(self) -> None
    def test_empty_title_handling(self) -> None
    def test_very_long_title_truncation(self) -> None
    def test_unicode_characters(self) -> None
```

### Implementation Function
```python
def generate_branch_name_from_issue(
    issue_number: int,
    issue_title: str,
    max_length: int = 244
) -> str
```

## HOW

### Integration Points
1. **Module Structure**: New file in `github_operations/` package
2. **Imports**: Standard library only (re, string)
3. **Standalone Function**: No dependencies on other classes
4. **Public API**: Will be imported by IssueBranchManager

### Sanitization Rules Implementation
```python
# 1. Replace " - " with "---"
# 2. Convert to lowercase
# 3. Replace spaces with "-"
# 4. Remove special characters (keep alphanumeric, -, _)
# 5. Strip leading/trailing dashes
# 6. Truncate if too long (preserve issue number)
```

## ALGORITHM

### Test Algorithm (key test cases)
```
# Test dash-space-dash conversion
Input: (123, "Fix - Database - Connection")
Expected: "123-fix---database---connection"

# Test length truncation
Input: (999, "A" * 300, max_length=20)
Expected: "999-aaaaaaaaaaaaaa" (length ≤ 20, preserves "999-")

# Test special characters
Input: (42, "Fix: Auth @User #123!")
Expected: "42-fix-auth-user-123"
```

### Implementation Algorithm
```
1. Create prefix: "{issue_number}-"
2. Apply sanitization to title:
   a. Replace " - " with "---"
   b. Convert to lowercase
   c. Replace spaces with "-"
   d. Keep only alphanumeric, -, _
   e. Strip leading/trailing dashes
3. Calculate available length: max_length - len(prefix)
4. Truncate title if needed
5. Return: prefix + sanitized_title
```

## DATA

### Input Parameters
- `issue_number: int` - Issue number (positive integer)
- `issue_title: str` - Raw issue title from GitHub
- `max_length: int` - Maximum branch name length (default: 244)

### Output
- `str` - Sanitized branch name in format: `{number}-{sanitized-title}`

### Examples
```python
# Basic case
(123, "Fix login bug") → "123-fix-login-bug"

# Dash-space-dash
(456, "Update - Config - File") → "456-update---config---file"

# Special characters
(789, "Add Feature: User Auth!") → "789-add-feature-user-auth"

# Long title (max_length=30)
(1, "This is a very long title that needs truncation") → "1-this-is-a-very-long-tit"

# Empty/whitespace title
(999, "   ") → "999"
```

## Implementation Structure

```python
"""Issue branch management for GitHub operations.

This module provides functionality for creating branches from issues
and querying linked branches via the GitHub API.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def generate_branch_name_from_issue(
    issue_number: int,
    issue_title: str,
    max_length: int = 244
) -> str:
    """Generate a GitHub-compatible branch name from an issue.
    
    Follows GitHub's branch naming conventions:
    - Format: {issue-number}-{sanitized-title}
    - " - " → "---" (three dashes)
    - Lowercase all text
    - Remove special characters (keep alphanumeric, dashes, underscores)
    - Spaces → "-"
    - Strip leading/trailing dashes
    - Truncate if exceeds max_length (preserving issue number)
    
    Args:
        issue_number: GitHub issue number
        issue_title: Issue title to sanitize
        max_length: Maximum branch name length (default: 244)
        
    Returns:
        Sanitized branch name
        
    Examples:
        >>> generate_branch_name_from_issue(123, "Fix login bug")
        '123-fix-login-bug'
        >>> generate_branch_name_from_issue(456, "Update - Config - File")
        '456-update---config---file'
    """
    # Implementation here following the algorithm
```

## Test File Structure

```python
"""Unit tests for IssueBranchManager."""

import pytest
from mcp_coder.utils.github_operations.issue_branch_manager import (
    generate_branch_name_from_issue,
)


class TestBranchNameGeneration:
    """Test branch name generation utility."""
    
    def test_basic_branch_name_generation(self) -> None:
        """Test basic branch name generation."""
        result = generate_branch_name_from_issue(123, "Fix login bug")
        assert result == "123-fix-login-bug"
    
    # More tests following...
```
