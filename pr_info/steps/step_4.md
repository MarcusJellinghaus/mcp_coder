# Step 4: Update CLI Prompt Command

## Objective
Update the CLI prompt command to use the shared CLI utility for consistent parameter handling across all CLI commands.

## WHERE
- **Modify**: `src/mcp_coder/cli/commands/prompt.py`
- **Update Tests**: `tests/cli/commands/test_prompt.py`

## WHAT
### Code to Update
```python
# Current prompt.py has duplicate parameter parsing:
def execute_prompt(args: argparse.Namespace) -> int:
    llm_method = getattr(args, "llm_method", "claude_code_api")
    provider, method = parse_llm_method(llm_method)  # Duplicate logic
    response = ask_llm(args.prompt, provider=provider, method=method, timeout=timeout)
```

### Import to Add
```python
from ..utils import parse_llm_method_from_args
```

### Function Call to Update
```python
# OLD (duplicate parsing logic):
llm_method = getattr(args, "llm_method", "claude_code_api")
provider, method = parse_llm_method(llm_method)

# NEW (using shared utility):
llm_method = getattr(args, "llm_method", "claude_code_api")
provider, method = parse_llm_method_from_args(llm_method)
```

### Existing Import to Remove
```python
# Remove direct import since we'll use shared utility:
from ...llm.session import parse_llm_method
```

## HOW
### Integration Points
```python
# Add import at top of file
from ..utils import parse_llm_method_from_args

# Update execute_prompt() function
llm_method = getattr(args, "llm_method", "claude_code_api")
provider, method = parse_llm_method_from_args(llm_method)

# All other code remains the same
response = ask_llm(args.prompt, provider=provider, method=method, timeout=timeout)
```

### Test Updates
```python
# Update tests to mock the shared utility
@patch("mcp_coder.cli.utils.parse_llm_method_from_args")
def test_execute_prompt(mock_parse):
    mock_parse.return_value = ("claude", "api")
    # Test continues as before
```

## ALGORITHM
```python
# Simple refactoring process:
1. Add import for shared CLI utility
2. Replace direct parse_llm_method() call with shared utility
3. Remove direct import of parse_llm_method
4. Update any tests that mock the parsing logic
5. Verify prompt command still works with both LLM methods
```

## DATA
### Files Modified
- Add 1 import line to `cli/commands/prompt.py`
- Update 1 function call in `execute_prompt()`
- Remove 1 import line from `cli/commands/prompt.py`
- Update test mocks if they mock parse_llm_method directly

### Code Duplication Eliminated
```python
# Before (duplicate parsing in each CLI command):
cli/commands/commit.py: provider, method = parse_llm_method(llm_method)
cli/commands/prompt.py: provider, method = parse_llm_method(llm_method)
cli/commands/implement.py: provider, method = parse_llm_method(llm_method)

# After (shared utility):
cli/commands/commit.py: provider, method = parse_llm_method_from_args(llm_method)
cli/commands/prompt.py: provider, method = parse_llm_method_from_args(llm_method)
cli/commands/implement.py: provider, method = parse_llm_method_from_args(llm_method)
```

### Import Structure
```python
# Updated imports in cli/commands/prompt.py:
from ..utils import parse_llm_method_from_args

# Removed import:
# from ...llm.session import parse_llm_method  (now via shared utility)
```

## LLM Prompt for Implementation

```
You are implementing Step 4 of the LLM parameter architecture improvement.

Reference the summary.md for full context. Your task is to update the CLI prompt command in `src/mcp_coder/cli/commands/prompt.py` to use the shared utility:

1. Add import for the shared CLI utility:
   - `from ..utils import parse_llm_method_from_args`

2. Update the `execute_prompt()` function to use shared utility:
   - Replace: `provider, method = parse_llm_method(llm_method)`
   - With: `provider, method = parse_llm_method_from_args(llm_method)`

3. Remove the direct import that's no longer needed:
   - Remove: `from ...llm.session import parse_llm_method`

4. Update any tests that directly mock `parse_llm_method` to mock the shared utility instead.

The goal is to eliminate code duplication and use consistent parameter handling across all CLI commands.

Key requirements:
- Use shared CLI utility for parameter conversion
- No behavior changes for end users
- All existing functionality preserved
- Tests updated to mock shared utility if needed
- Prompt command works with both claude_code_cli and claude_code_api
```
