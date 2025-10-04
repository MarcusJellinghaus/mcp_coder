# Step 3: Update CLI Commit Command

## Objective
Update the CLI commit command to use the shared CLI utility and the moved commit function with structured parameters.

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

### Imports to Add
```python
from ..utils import parse_llm_method_from_args
from ...utils.commit_operations import generate_commit_message_with_llm
```

### Function Call Updates
```python
# OLD (string parameter):
success, commit_message, error = generate_commit_message_with_llm(
    project_dir, args.llm_method
)

# NEW (structured parameters):
provider, method = parse_llm_method_from_args(args.llm_method)
success, commit_message, error = generate_commit_message_with_llm(
    project_dir, provider, method
)
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
# Remove existing function definition (~80 lines)
# Add imports at top of file
from ..utils import parse_llm_method_from_args
from ...utils.commit_operations import generate_commit_message_with_llm

# Update function calls in execute_commit_auto()
provider, method = parse_llm_method_from_args(args.llm_method)
success, commit_message, error = generate_commit_message_with_llm(
    project_dir, provider, method
)
```

### Test Updates
```python
# Update mock patch paths in tests
# OLD:
@patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")

# NEW:
@patch("mcp_coder.utils.commit_operations.generate_commit_message_with_llm")
@patch("mcp_coder.cli.utils.parse_llm_method_from_args")
```

## ALGORITHM
```python
# CLI integration fix:
1. Remove function definition from cli/commands/commit.py (~80 lines)
2. Add imports for CLI utility and utils module
3. Update execute_commit_auto() to use shared utility for parameter conversion
4. Update function call to use structured parameters
5. Update all test mock paths for moved function
6. Verify all CLI behavior remains identical
```

## DATA
### Files Modified
- Remove ~80 lines from `cli/commands/commit.py` (function definition)
- Add 2 import lines to `cli/commands/commit.py`
- Update ~5 mock patch decorators in test files
- Update function call in `execute_commit_auto()`

### Parameter Flow Changes
```python
# Before (string parameter):
args.llm_method → generate_commit_message_with_llm(project_dir, args.llm_method)

# After (structured parameters):
args.llm_method → parse_llm_method_from_args() → (provider, method) → 
generate_commit_message_with_llm(project_dir, provider, method)
```

### Import Structure
```python
# New imports in cli/commands/commit.py:
from ..utils import parse_llm_method_from_args
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
You are implementing Step 3 of the LLM parameter architecture improvement.

Reference the summary.md for full context. Your task is to update the CLI commit command in `src/mcp_coder/cli/commands/commit.py`:

1. Remove the `generate_commit_message_with_llm()` function since it was moved to utils in Step 2.

2. Add imports for the shared utility and moved function:
   - `from ..utils import parse_llm_method_from_args`
   - `from ...utils.commit_operations import generate_commit_message_with_llm`

3. Update `execute_commit_auto()` to use the new parameter flow:
   - Parse: `provider, method = parse_llm_method_from_args(args.llm_method)`
   - Call: `generate_commit_message_with_llm(project_dir, provider, method)`

4. Update test files to mock the function from its new location and add mock for CLI utility.

The goal is to make the CLI use the shared utility and moved function transparently. All CLI behavior must remain identical.

Key requirements:
- Remove only the function definition, keep all other helper functions
- Use shared CLI utility for parameter conversion
- Update function calls to use structured parameters
- Update all test mock paths
- All existing tests must pass with no behavior changes
```
