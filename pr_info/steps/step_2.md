# Step 2: Update CLI Command to Use New Module

## Objective
Update the CLI commit command to import from the new utils module instead of having the function locally.

## WHERE
- **Modify**: `src/mcp_coder/cli/commands/commit.py`
- **Update Tests**: `tests/cli/commands/test_commit.py`

## WHAT
### Function to Remove
```python
def generate_commit_message_with_llm(
    project_dir: Path, llm_method: str = "claude_code_api"
) -> Tuple[bool, str, Optional[str]]:
    # Remove this entire function - it's now in utils
```

### Import to Add
```python
from ...utils.commit_operations import generate_commit_message_with_llm
```

### Helper Functions to Keep
```python
def parse_llm_commit_response(response: str) -> Tuple[str, Optional[str]]
def validate_git_repository(project_dir: Path) -> Tuple[bool, Optional[str]]
def execute_commit_auto(args: argparse.Namespace) -> int
def execute_commit_clipboard(args: argparse.Namespace) -> int
def get_commit_message_from_clipboard() -> Tuple[bool, str, Optional[str]]
```

## HOW
### Integration Points
```python
# Remove existing function definition
# Add import at top of file
from ...utils.commit_operations import generate_commit_message_with_llm

# All existing calls remain the same:
success, commit_message, error = generate_commit_message_with_llm(
    project_dir, args.llm_method
)
```

### Test Updates
```python
# Update mock patch paths in tests
# OLD:
@patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")

# NEW:  
@patch("mcp_coder.utils.commit_operations.generate_commit_message_with_llm")
```

## ALGORITHM
```python
# No algorithm changes - just import/remove:
1. Remove function definition from cli/commands/commit.py
2. Add import from utils.commit_operations
3. Update all test mock paths
4. Verify all calls still work identically
5. Run tests to ensure no regression
```

## DATA
### Files Modified
- Remove ~50 lines from `cli/commands/commit.py` (function definition)
- Add 1 import line to `cli/commands/commit.py`
- Update ~5 mock patch decorators in test files

### Function Calls (Unchanged)
```python
# These calls remain identical:
success, commit_message, error = generate_commit_message_with_llm(
    project_dir, args.llm_method
)
```

### Import Structure
```python
# New import in cli/commands/commit.py:
from ...utils.commit_operations import generate_commit_message_with_llm

# Dependencies (unchanged):
from ...utils.git_operations import (
    commit_staged_files,
    get_git_diff_for_commit,
    is_git_repository,
    stage_all_changes,
)
```

## LLM Prompt for Implementation

```
You are implementing Step 2 of the commit auto function architecture fix.

Reference the summary.md for full context. Your task is to:

1. Remove the `generate_commit_message_with_llm()` function from `src/mcp_coder/cli/commands/commit.py` since it was moved to utils in Step 1.

2. Add the import: `from ...utils.commit_operations import generate_commit_message_with_llm`

3. Update test files to mock the function from its new location:
   - Change `@patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")` 
   - To `@patch("mcp_coder.utils.commit_operations.generate_commit_message_with_llm")`

4. Verify all existing function calls remain identical - no behavior changes.

The goal is to make the CLI use the moved function transparently. All existing functionality must work exactly the same.

Key requirements:
- Remove only the function definition, keep all other helper functions
- Add correct import with relative path
- Update all test mock paths
- No changes to function calls or behavior
- All existing tests must pass
```
