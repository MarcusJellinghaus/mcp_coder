# Step 7: Refactor Managers to Use BaseGitHubManager

## Context
Update both `LabelsManager` and `PullRequestManager` to inherit from `BaseGitHubManager`, removing duplicated initialization code while maintaining all existing functionality.

## WHERE

### Files to Modify
```
src/mcp_coder/utils/github_operations/labels_manager.py
src/mcp_coder/utils/github_operations/pr_manager.py
```

## WHAT

### Class Inheritance Changes

```python
# labels_manager.py
from .base_manager import BaseGitHubManager

class LabelsManager(BaseGitHubManager):
    def __init__(self, project_dir: Optional[Path] = None) -> None:
        super().__init__(project_dir)
        # Remove duplicated initialization code
    
    # Keep all existing methods unchanged
```

```python  
# pr_manager.py
from .base_manager import BaseGitHubManager

class PullRequestManager(BaseGitHubManager):
    def __init__(self, project_dir: Optional[Path] = None) -> None:
        super().__init__(project_dir)
        # Remove duplicated initialization code
    
    # Keep all existing methods unchanged
```

## HOW

### Integration Points
- Import `BaseGitHubManager` in both files
- Change class declarations to inherit from base class
- Replace `__init__` methods with `super().__init__(project_dir)` call
- Remove duplicated helper methods that now exist in base class
- Keep all public methods and their signatures unchanged

### Code Removal
Remove these duplicated methods from both classes:
- Manual project_dir validation
- Manual GitHub token retrieval
- Manual git repository initialization
- Manual GitHub client setup
- `_get_repository()` method (now in base)

## ALGORITHM

### Refactoring Process
```
1. Add import for BaseGitHubManager in both files
2. Change class inheritance: class Manager(BaseGitHubManager)
3. Replace __init__ with super().__init__(project_dir) call
4. Remove duplicated initialization code
5. Remove duplicated helper methods (_get_repository, etc.)
```

## DATA

### Removed Code Sections
- Project directory validation logic
- GitHub token retrieval from config
- Git repository initialization with error handling
- GitHub client instantiation
- Repository URL parsing and caching logic

### Maintained Functionality
- All public method signatures remain identical
- All method behavior remains unchanged
- All error handling patterns preserved
- All return types and data structures unchanged

## LLM Prompt

```
Refactor LabelsManager and PullRequestManager to inherit from BaseGitHubManager.

Context: Read pr_info/steps/summary.md and pr_info/steps/decisions.md for overview.
Reference: Step 6 created BaseGitHubManager with shared functionality

Tasks:
1. Update labels_manager.py:
   - Add import: from .base_manager import BaseGitHubManager
   - Change class declaration: class LabelsManager(BaseGitHubManager)
   - Replace __init__ with super().__init__(project_dir) call
   - Remove duplicated initialization code
   - Remove duplicated _get_repository() method
   - Keep all other methods unchanged

2. Update pr_manager.py:
   - Add import: from .base_manager import BaseGitHubManager  
   - Change class declaration: class PullRequestManager(BaseGitHubManager)
   - Replace __init__ with super().__init__(project_dir) call
   - Remove duplicated initialization code
   - Remove duplicated _get_repository() method
   - Keep all other methods unchanged

Implementation notes:
- This is a pure refactoring - no functional changes
- All public method signatures must remain identical
- All error handling and validation logic preserved in base class
- Remove only the duplicated code, keep manager-specific methods

Run tests:
1. pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v
2. pytest tests/utils/test_github_operations.py::TestPullRequestManagerUnit -v
Expected: All tests PASS (no behavioral changes from inheritance refactor)
```

## Notes

- Critical: This is a pure refactor with zero functional changes
- All existing tests must pass without modification
- All public APIs remain identical
- Only initialization code is consolidated into base class
- Manager-specific methods (CRUD operations) remain in respective classes
