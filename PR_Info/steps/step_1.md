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
# Remove handle_no_command() function
# Update get_help_text() to be the primary help function
# Remove get_usage_examples() and related example code
# Simplify help text generation
```

## HOW
- **Code Removal**: Remove `handle_no_command()` function entirely
- **Function Update**: Make `get_help_text()` the main help function
- **Cleanup**: Remove example generation code
- **Integration**: Update any callers to use `get_help_text()` directly

## ALGORITHM
```
1. REMOVE handle_no_command() function
2. UPDATE get_help_text() to be standalone (no examples)
3. REMOVE get_usage_examples() function
4. CLEAN UP any example-related imports or code
5. VERIFY help system still works correctly
```

## DATA
**Function to Remove**:
```python
def handle_no_command() -> None:
    # This entire function should be removed
```

**Function to Update**:
```python
def get_help_text() -> str:
    """Return help text without examples."""
    # Update implementation to be simpler
```

**Expected Result**:
- Simplified help system
- No example generation in help functions
- Clean foundation for documentation updates
- Maintained help functionality for users
