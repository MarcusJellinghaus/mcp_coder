# Step 2: Create GitHub Operations Module Structure

## Objective
Create the github_operations.py module with function signatures and docstrings (TDD: empty implementations).

## WHERE
- File: `src/mcp_coder/utils/github_operations.py` (new file)

## WHAT
- Three core functions with proper signatures and docstrings
- Import statements for required dependencies
- Placeholder implementations that return empty dicts

## HOW
### Module Structure
```python
"""GitHub pull request operations for MCP Coder."""

from typing import Optional
from mcp_coder.utils.log_utils import log_function_call
from mcp_coder.utils.user_config import get_config_value

@log_function_call
def create_pull_request(title: str, body: str, head: str, base: str = "main") -> dict:
    """Create a pull request."""
    return {}

@log_function_call  
def get_pull_request(pr_number: int) -> dict:
    """Get pull request details."""
    return {}

@log_function_call
def close_pull_request(pr_number: int) -> dict:
    """Close a pull request.""" 
    return {}
```

## ALGORITHM
```
1. Create new file in src/mcp_coder/utils/
2. Add module docstring and imports
3. Define three functions with @log_function_call decorator
4. Add comprehensive docstrings with Args/Returns
5. Return empty dict {} for TDD approach
```

## DATA
- **Input**: Function parameters (title, body, head, base, pr_number)
- **Output**: Empty dictionaries (placeholder for TDD)
- **Expected final returns**:
  - create_pull_request: `{'number': int, 'url': str}`
  - get_pull_request: `{'number': int, 'title': str, 'state': str, 'url': str}`
  - close_pull_request: `{'number': int, 'state': str}`

## LLM Prompt
```
You are implementing Step 2 of the GitHub Pull Request Operations feature as described in pr_info/steps/summary.md.

Create src/mcp_coder/utils/github_operations.py with the three core functions following TDD approach - define signatures and docstrings but return empty dicts.

Requirements:
- Create the three functions: create_pull_request, get_pull_request, close_pull_request
- Use @log_function_call decorator on all functions (import from mcp_coder.utils.log_utils)
- Import get_config_value from mcp_coder.utils.user_config
- Add comprehensive docstrings following project patterns
- Return empty dict {} from each function (TDD placeholder)
- Follow existing code style and type hints

This is the skeleton that will drive our test implementation in the next step.
```

## Verification
- [ ] File created at correct path
- [ ] Three functions defined with correct signatures
- [ ] @log_function_call decorator applied
- [ ] Comprehensive docstrings added
- [ ] Type hints included
- [ ] Functions return empty dicts
- [ ] Required imports present
