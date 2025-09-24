# Step 3: Export Function and Update Documentation

## LLM Prompt
```
Review the summary document at pr_info/steps/summary.md and previous steps for context.

Implement Step 3: Export the new `git_push()` function in the public API and add a simple usage example to README.md. Follow the existing patterns for exporting git operations and keep documentation minimal and focused.
```

## WHERE
- **File 1**: `src/mcp_coder/__init__.py`
- **File 2**: `README.md`
- **Location**: Add to existing git operations imports and examples

## WHAT
- **Export Function**: Add `git_push` to public API imports
- **Documentation**: Add simple commit + push workflow example
- **Integration**: Place alongside existing git operation exports

## HOW
- **Import Statement**: Add to existing git operations import block
- **README Section**: Add to existing "Git Operations" section
- **Example Code**: Show typical commit → push workflow
- **Consistency**: Follow existing documentation patterns

## ALGORITHM
```
1. Add git_push to __init__.py imports
2. Update README.md Git Operations section
3. Add simple usage example showing workflow
4. Keep documentation concise and focused
5. Follow existing code example formatting
```

## DATA
- **Import Addition**: `git_push` function from `utils.git_operations`
- **Documentation**: Code example showing commit + push workflow
- **Example Return Values**: Show success/error handling pattern

## Implementation Details

### __init__.py Changes
```python
# Add to existing git operations imports
from .utils.git_operations import (
    # ... existing imports ...
    git_push,  # Add this line
)
```

### README.md Changes
Add to existing "Git Operations" section:
```python
# Complete commit + push workflow
commit_result = commit_all_changes("Add new feature", repo_path)
if commit_result["success"]:
    push_result = git_push(repo_path)
    if push_result["success"]:
        print("Successfully committed and pushed changes")
    else:
        print(f"Push failed: {push_result['error']}")
```

### Integration Points
- Place import alphabetically with existing git operations
- Add example to existing Git Operations section in README
- Maintain consistency with existing code examples
- No new documentation sections needed - extend existing ones

### API Reference Update
Add simple entry to existing git operations documentation:

#### `git_push(repo_path)`
Push current branch to origin remote.

**Parameters:**
- `repo_path` (Path): Path to the git repository

**Returns:** Dictionary with success status and error details
