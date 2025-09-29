# Step 9: Integration and Module Export

## Objective
Export IssueManager class from the github_operations module to make it available for import alongside PullRequestManager.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/__init__.py`

## WHAT
Add IssueManager to module exports:
```python
from .issue_manager import IssueManager
```

## HOW
- Follow the exact same pattern as PullRequestManager export
- Add to existing __init__.py file
- Maintain alphabetical ordering in imports

## ALGORITHM
```
1. Open existing __init__.py file
2. Add import for IssueManager from .issue_manager
3. Add IssueManager to __all__ list (if present)
4. Maintain consistent formatting with existing imports
```

## DATA
```python
# Module exports after change
from mcp_coder.utils.github_operations import PullRequestManager, IssueManager
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 9: Integration and Module Export.

Update src/mcp_coder/utils/github_operations/__init__.py to export the new IssueManager class.

Requirements:
- Add import for IssueManager following the same pattern as PullRequestManager
- Maintain consistent code style and formatting
- Keep imports in alphabetical order
- Add to __all__ list if one exists

This should be a simple 1-2 line addition to make IssueManager importable.
```
