# Step 6: Update Utils Module Exports and Documentation

## Objective
Export PullRequestManager from utils module and update documentation to complete the integration.

## WHERE
- File: `src/mcp_coder/utils/__init__.py` (modify existing)
- File: `tests/README.md` (modify existing)

## WHAT
- Add PullRequestManager and create_pr_manager to utils module exports
- Update test documentation with github_integration marker usage
- Final integration verification and cleanup

## HOW
### Utils Module Export
```python
# Add to imports section
from .github_operations import (
    PullRequestManager,
    create_pr_manager,
)

# Add to __all__ list
__all__ = [
    # ... existing exports ...
    # GitHub operations
    "PullRequestManager",
    "create_pr_manager",
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
2. Add import statement for PullRequestManager and create_pr_manager
3. Add class and function names to __all__ list with comment
4. Open tests/README.md
5. Add github_integration row to markers table
6. Verify imports work correctly
7. Test final integration
```

## DATA
- **Imports**: PullRequestManager class and create_pr_manager function from github_operations module
- **Exports**: Class and function names added to __all__ list
- **Documentation**: Marker description and requirements for GitHub integration tests

## LLM Prompt
```
You are implementing Step 6 of the GitHub Pull Request Operations feature using the updated PullRequestManager approach.

Update the module exports and documentation to complete the integration.

Requirements:
1. Add imports to src/mcp_coder/utils/__init__.py:
   - Import PullRequestManager and create_pr_manager from .github_operations
   - Add these to the __all__ list with a "# GitHub operations" comment
   - Follow the existing import and export patterns in the file

2. Update tests/README.md:
   - Add github_integration marker to the test markers table
   - Follow the existing table format and style
   - Mention GitHub config requirement

3. Final verification:
   - Ensure PullRequestManager can be imported as: from mcp_coder.utils import PullRequestManager
   - Verify create_pr_manager factory function is also importable
   - Run all tests to ensure integration works correctly

Keep changes minimal and follow existing patterns. Complete the feature integration.
```

## Verification
- [ ] PullRequestManager imported in utils/__init__.py
- [ ] create_pr_manager imported in utils/__init__.py
- [ ] Both added to __all__ list with GitHub operations comment
- [ ] tests/README.md updated with github_integration marker info
- [ ] PullRequestManager can be imported from mcp_coder.utils
- [ ] create_pr_manager can be imported from mcp_coder.utils
- [ ] Documentation follows existing format
- [ ] All integration tests pass
- [ ] Final feature integration complete
