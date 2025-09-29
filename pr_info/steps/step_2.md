# Step 2: Implement LabelsManager Class with Initialization

## Context
Implement LabelsManager class to make Step 1 unit tests pass. Focus on initialization and validation only - CRUD operations come in Step 4.

## WHERE

### New File
```
src/mcp_coder/utils/github_operations/labels_manager.py
```

### Update Exports
```
src/mcp_coder/utils/github_operations/__init__.py
```

## WHAT

### Main Class and TypedDict

```python
class LabelData(TypedDict):
    name: str
    color: str
    description: str
    url: str

class LabelsManager:
    def __init__(self, project_dir: Optional[Path] = None) -> None
    def _validate_label_name(self, name: str) -> bool
    def _validate_color(self, color: str) -> bool
    def _parse_and_get_repo(self) -> Optional[Repository]
```

## HOW

### Imports
```python
import logging
import re
from pathlib import Path
from typing import Optional, TypedDict

from github import Github
from github.GithubException import GithubException
from github.Repository import Repository

from mcp_coder.utils.log_utils import log_function_call
from .github_utils import parse_github_url
```

### Integration Points
- Reuse validation logic from `PullRequestManager.__init__()`
- Use `get_config_value("github", "token")` for token
- Use `log_function_call` decorator on public methods

## ALGORITHM

### Initialization Logic
```
1. Validate: project_dir is not None and exists and is directory
2. Validate: directory is git repository (use is_git_repository)
3. Get: GitHub repository URL from git remote
4. Get: GitHub token from config (get_config_value)
5. Initialize: Github client and cache repository URL/token
```

### Label Name Validation
```
1. Check: name is string and not empty/whitespace only
2. Check: name has no leading/trailing whitespace
3. Return: True if valid, False otherwise (log error)
Note: Allows spaces, hyphens, underscores, emojis, special chars (GitHub is permissive)
```

### Color Validation
```
1. Strip: leading '#' character if present for user convenience
2. Check: remaining string has exactly 6 characters
3. Check: all characters are hex digits (0-9, A-F, a-f)
4. Return: True if valid, False otherwise (log error)
Note: Accepts both "FF0000" and "#FF0000", normalizes to "FF0000"
```

## DATA

### Instance Attributes
```python
self.project_dir: Path
self.repository_url: str
self.github_token: str
self._github_client: Github
self._repository: Optional[Repository] = None
```

### Validation Return Values
- `_validate_label_name(name)`: `bool` (True if valid)
- `_validate_color(color)`: `bool` (True if valid)
- `_parse_and_get_repo()`: `Optional[Repository]` (None on error)

## LLM Prompt

```
Implement LabelsManager class initialization and validation to make Step 1 tests pass.

Context: Read pr_info/steps/summary.md for overview.
Reference: src/mcp_coder/utils/github_operations/pr_manager.py -> PullRequestManager class

Tasks:
1. Create labels_manager.py with LabelData TypedDict and LabelsManager class
2. Implement __init__ following same pattern as PullRequestManager
3. Implement _validate_label_name (non-empty, no leading/trailing whitespace - allows spaces, special chars, emojis)
4. Implement _validate_color (6-char hex string, accepts both "FF0000" and "#FF0000" formats - normalize by stripping # prefix)
5. Implement _parse_and_get_repo (same pattern as PullRequestManager)
6. Update __init__.py to export LabelsManager and LabelData

Implementation notes:
- Use same validation helpers: is_git_repository, get_github_repository_url
- Use get_config_value("github", "token") for token
- Log errors using logger.error() for validation failures
- DO NOT implement CRUD methods yet (Step 4)

Run: pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v
Expected: All tests PASS (green phase)
```

## Notes

- Copy initialization pattern from PullRequestManager exactly
- Label name validation: non-empty, no leading/trailing whitespace (allows spaces, hyphens, underscores, emojis, special chars)
- Color validation: exactly 6 hex characters (accept upper/lower case, with or without # prefix)
- Strip # prefix during validation and when sending to GitHub API
- No CRUD methods yet - just setup and validation
- Update `__init__.py` to export new classes
