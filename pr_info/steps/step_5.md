# Step 5: Export Functions and Update Documentation

## Objective
Export the new GitHub operations from utils module and update test documentation.

## WHERE
- File: `src/mcp_coder/utils/__init__.py` (modify existing)
- File: `tests/README.md` (modify existing)

## WHAT
- Add GitHub operations to utils module exports
- Update test documentation with github_integration marker usage

## HOW
### Utils Module Export
```python
# Add to imports section
from .github_operations import (
    create_pull_request,
    get_pull_request,
    close_pull_request,
    list_pull_requests,
)

# Add to __all__ list
__all__ = [
    # ... existing exports ...
    # GitHub operations
    "create_pull_request", 
    "get_pull_request",
    "close_pull_request",
    "list_pull_requests",
]
```

### Documentation Update
Add section to tests/README.md:
```markdown
| `github_integration` | GitHub API calls | Variable | GitHub config |
```

## ALGORITHM
```
1. Open src/mcp_coder/utils/__init__.py
2. Add import statement for three GitHub functions
3. Add function names to __all__ list with comment
4. Open tests/README.md
5. Add github_integration row to markers table
6. Verify imports work correctly
```

## DATA
- **Imports**: Three function names from github_operations module
- **Exports**: Function names added to __all__ list
- **Documentation**: Marker description and requirements

## LLM Prompt
```
You are implementing Step 5 of the GitHub Pull Request Operations feature as described in pr_info/steps/summary.md.

Update the module exports and documentation to complete the integration.

Requirements:
1. Add imports to src/mcp_coder/utils/__init__.py:
   - Import create_pull_request, get_pull_request, close_pull_request, list_pull_requests from .github_operations
   - Add these four functions to the __all__ list with a "# GitHub operations" comment
   - Follow the existing import and export patterns in the file

2. Update tests/README.md:
   - Add github_integration marker to the test markers table
   - Follow the existing table format and style
   - Mention GitHub config requirement

Keep changes minimal and follow existing patterns. The functions should now be importable as:
from mcp_coder.utils import create_pull_request, get_pull_request, close_pull_request, list_pull_requests
```

## Verification
- [ ] Functions imported in utils/__init__.py
- [ ] Functions added to __all__ list
- [ ] GitHub operations comment added
- [ ] tests/README.md updated with marker info
- [ ] Functions can be imported from mcp_coder.utils
- [ ] Documentation follows existing format
- [ ] All integration tests pass
