# Step 1: Refactor Help System

## LLM Prompt
```
Refactor the help system by replacing handle_no_command() with get_help_text() and removing examples from help functions. This is a prerequisite for clean documentation updates in the --continue-from-last feature.

Reference: PR_Info/steps/summary.md and PR_Info/steps/Decisions.md

This is step 1 of 7: Help system refactoring before implementing the main feature.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/help.py`
- **Function**: Replace `handle_no_command()` with `get_help_text()`
- **Cleanup**: Remove example-related code from help functions

## WHAT
**Main changes**:
```python
# Add parameter to get_help_text(include_examples: bool = False)
# Update execute_help() to call get_help_text(include_examples=True)
# Update handle_no_command() to call get_help_text(include_examples=False)
# Keep get_usage_examples() but only call it when include_examples=True
```

## HOW
- **Function Update**: Add `include_examples` parameter to `get_help_text()`
- **Help Command**: Update `execute_help()` to call with `include_examples=True`
- **No Command**: Update `handle_no_command()` to call with `include_examples=False`
- **Conditional Logic**: Only call `get_usage_examples()` when `include_examples=True`

## ALGORITHM
```
1. ADD include_examples parameter to get_help_text() with default False
2. UPDATE get_help_text() to conditionally include examples based on parameter
3. UPDATE execute_help() to call get_help_text(include_examples=True)
4. UPDATE handle_no_command() to call get_help_text(include_examples=False)
5. VERIFY both help scenarios work correctly
```

## DATA
**Function to Update**:
```python
def get_help_text(include_examples: bool = False) -> str:
    """Get help text with optional examples.
    
    Args:
        include_examples: If True, include usage examples section
    """
    # Implementation with conditional examples
```

**Updated Callers**:
```python
# In execute_help()
help_text = get_help_text(include_examples=True)

# In handle_no_command()
help_text = get_help_text(include_examples=False)
```

**Expected Result**:
- Single parameterized help function
- Examples shown in help command but not in no-command scenario
- Clean foundation for documentation updates
- Maintained help functionality for users
