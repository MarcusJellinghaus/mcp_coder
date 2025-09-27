# Step 2: Create GitHub Operations Module Structure

## Objective
Create the github_operations.py module with function signatures and docstrings (TDD: empty implementations).

## WHERE
- Files: 
  - `src/mcp_coder/utils/github_operations/__init__.py` (new file)
  - `src/mcp_coder/utils/github_operations/gh_pull_requests.py` (new file)

## WHAT
- Four core functions with proper signatures and docstrings
- Package structure with proper exports
- Import statements for required dependencies
- Placeholder implementations that return empty dicts/lists

## HOW
### Package Structure
**__init__.py:**
```python
"""GitHub operations for MCP Coder."""

from .gh_pull_requests import (
    create_pull_request,
    get_pull_request,
    close_pull_request,
    list_pull_requests,
)

__all__ = [
    "create_pull_request",
    "get_pull_request", 
    "close_pull_request",
    "list_pull_requests",
]
```

**gh_pull_requests.py:**
```python
"""GitHub pull request operations for MCP Coder."""

from typing import Optional
from mcp_coder.utils.log_utils import log_function_call
from mcp_coder.utils.user_config import get_config_value

@log_function_call
def create_pull_request(repo_url: str, title: str, body: str, head: str, base: str = "main") -> dict:
    """Create a pull request."""
    return {}

@log_function_call  
def get_pull_request(repo_url: str, pr_number: int) -> dict:
    """Get pull request details."""
    return {}

@log_function_call
def close_pull_request(repo_url: str, pr_number: int) -> dict:
    """Close a pull request.""" 
    return {}

@log_function_call
def list_pull_requests(repo_url: str, state: str = "open") -> list:
    """List pull requests."""
    return []
```

## ALGORITHM
```
1. Create new package directory in src/mcp_coder/utils/
2. Create __init__.py with exports
3. Create gh_pull_requests.py with module docstring and imports
4. Define four functions with @log_function_call decorator
5. Add comprehensive docstrings with Args/Returns
6. Return empty dict/list {} for TDD approach
```

## DATA
- **Input**: Function parameters (title, body, head, base, pr_number, state)
- **Output**: Empty dictionaries/lists (placeholder for TDD)
- **Expected final returns**:
  - create_pull_request: `{'number': int, 'url': str}`
  - get_pull_request: `{'number': int, 'title': str, 'state': str, 'url': str}`
  - close_pull_request: `{'number': int, 'state': str}`
  - list_pull_requests: `[{'number': int, 'title': str, 'state': str}]`

## LLM Prompt
```
You are implementing Step 2 of the GitHub Pull Request Operations feature as described in pr_info/steps/summary.md.

Create the GitHub operations package with four core functions following TDD approach - define signatures and docstrings but return empty dicts/lists.

Requirements:
- Create package structure: github_operations/__init__.py + github_operations/gh_pull_requests.py
- Create four functions: create_pull_request, get_pull_request, close_pull_request, list_pull_requests
- Use @log_function_call decorator on all functions (import from mcp_coder.utils.log_utils)
- Import get_config_value from mcp_coder.utils.user_config
- Add comprehensive docstrings following project patterns
- Return empty dict {} or list [] from each function (TDD placeholder)
- Proper package exports in __init__.py
- Follow existing code style and type hints

This is the skeleton that will drive our test implementation in the next step.
```

## Verification
- [ ] Package directory created at correct path
- [ ] __init__.py created with proper exports
- [ ] gh_pull_requests.py created with four functions
- [ ] Four functions defined with correct signatures
- [ ] @log_function_call decorator applied
- [ ] Comprehensive docstrings added
- [ ] Type hints included
- [ ] Functions return empty dicts/lists
- [ ] Required imports present
