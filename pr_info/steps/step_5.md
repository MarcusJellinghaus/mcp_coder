# Step 5: Update Exports and Documentation

## LLM Prompt
```
Read pr_info/steps/summary.md and this step file. Update module exports and documentation to integrate the new IssueBranchManager:
1. Update __init__.py to export new classes and functions
2. Update ARCHITECTURE.md to document the new manager
No new tests needed - this is integration/documentation only.
```

## WHERE
- **Module Exports**: `src/mcp_coder/utils/github_operations/__init__.py`
- **Documentation**: `docs/architecture/ARCHITECTURE.md`

## WHAT

### Files to Modify
1. `__init__.py` - Add exports for new components
2. `ARCHITECTURE.md` - Document IssueBranchManager in appropriate sections

## HOW

### 1. Update Module Exports

**File**: `src/mcp_coder/utils/github_operations/__init__.py`

Add to imports:
```python
from .issue_branch_manager import (
    BranchCreationResult,
    IssueBranchManager,
    generate_branch_name_from_issue,
)
```

Add to `__all__`:
```python
__all__ = [
    "BaseGitHubManager",
    "PullRequestManager",
    "LabelsManager",
    "IssueManager",
    "IssueBranchManager",           # NEW
    "LabelData",
    "IssueData",
    "CommentData",
    "BranchCreationResult",         # NEW
    "generate_branch_name_from_issue",  # NEW (optional - if public API)
]
```

### 2. Update Architecture Documentation

**File**: `docs/architecture/ARCHITECTURE.md`

**Section**: "Building Block View" → "Automation & Operations"

Add after the `issue_manager.py` description:

```markdown
  - `issue_branch_manager.py` - Issue-branch operations (tests: `test_issue_branch_manager.py`)
    - Branch creation from issues via GitHub API
    - Branch name generation with GitHub sanitization rules
    - Linked branch querying via timeline events
```

**Section**: Same section, update the list to include:

```markdown
- **GitHub integration**: `utils/github_operations/` - API interactions (tests: `utils/github_operations/test_*.py` 🏷️ github_integration)
  - `base_manager.py` - Base class for GitHub managers
  - `github_utils.py` - GitHub URL parsing and validation
  - `issue_manager.py` - Issue management operations (tests: `test_issue_manager.py`, `test_issue_manager_integration.py`)
  - `issue_branch_manager.py` - Issue-branch operations (tests: `test_issue_branch_manager.py`)
  - `labels_manager.py` - Label management operations (tests: `test_labels_manager.py`)
  - `pr_manager.py` - Pull request management via PyGithub API (tests: `test_pr_manager.py`)
  - Smoke tests: `test_github_integration_smoke.py` - Basic GitHub API connectivity validation
```

## DATA

### Module Structure After Changes

```
src/mcp_coder/utils/github_operations/
├── __init__.py              [MODIFIED] - Exports IssueBranchManager
├── base_manager.py          [unchanged]
├── github_utils.py          [unchanged]
├── issue_manager.py         [MODIFIED in Step 1] - Added get_issue()
├── issue_branch_manager.py  [NEW in Steps 2-4] - Branch operations
├── labels_manager.py        [unchanged]
└── pr_manager.py            [unchanged]
```

### Public API Exports

After this step, users can import:
```python
from mcp_coder.utils.github_operations import (
    IssueBranchManager,
    BranchCreationResult,
    generate_branch_name_from_issue,  # If exported as public API
)
```

## Implementation Checklist

### __init__.py Changes
- [ ] Add import statement for `issue_branch_manager` module
- [ ] Add `IssueBranchManager` to `__all__`
- [ ] Add `BranchCreationResult` to `__all__`
- [ ] (Optional) Add `generate_branch_name_from_issue` to `__all__` if public API
- [ ] Verify no import errors with `python -c "from mcp_coder.utils.github_operations import IssueBranchManager"`

### ARCHITECTURE.md Changes
- [ ] Add `issue_branch_manager.py` to GitHub integration list
- [ ] Include brief description of functionality
- [ ] Reference test file location
- [ ] Maintain consistent formatting with existing entries
- [ ] Update any relevant diagrams if needed

## Verification

### Import Verification Script
```python
# Test that all exports work correctly
from mcp_coder.utils.github_operations import (
    BaseGitHubManager,
    PullRequestManager,
    LabelsManager,
    IssueManager,
    IssueBranchManager,
    LabelData,
    IssueData,
    CommentData,
    BranchCreationResult,
)

print("✓ All imports successful")
```

### Documentation Verification
- Check that markdown renders correctly
- Verify links to test files are accurate
- Ensure consistent formatting with surrounding sections

## Complete __init__.py After Changes

```python
"""GitHub operations module for MCP Coder.

This module provides GitHub API integration functionality for managing
pull requests, labels, issues, and branch operations.
"""

from .base_manager import BaseGitHubManager
from .issue_branch_manager import (
    BranchCreationResult,
    IssueBranchManager,
    generate_branch_name_from_issue,
)
from .issue_manager import CommentData, IssueData, IssueManager
from .labels_manager import LabelData, LabelsManager
from .pr_manager import PullRequestManager

__all__ = [
    "BaseGitHubManager",
    "PullRequestManager",
    "LabelsManager",
    "IssueManager",
    "IssueBranchManager",
    "LabelData",
    "IssueData",
    "CommentData",
    "BranchCreationResult",
    "generate_branch_name_from_issue",
]
```

## Notes

- This step has no test implementation since it's purely integration
- Verify imports work before committing
- Run pylint to ensure no import issues
- Check that documentation renders properly in markdown viewers
