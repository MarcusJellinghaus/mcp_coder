# Step 1: Setup Project Structure and Dependencies

## Objective
Set up the project structure for the refactored LLM interface and add the necessary dependency for Claude Code Python SDK.

## WHERE
- `pyproject.toml` - Add claude-code-sdk dependency
- `pr_info/steps/` - Create directory structure for implementation plan

## WHAT
### Main Changes:
- Add `claude-code-sdk` to dependencies
- Create directory structure for step-by-step implementation

### Function Signatures:
No new functions in this step - only project setup.

## HOW
### Integration Points:
- Add dependency to `[project.dependencies]` section
- Ensure compatibility with existing Python 3.11+ requirement

### Dependencies:
```toml
dependencies = [
    "claude-code-sdk",  # New dependency for Python SDK
]
```

## ALGORITHM
```pseudocode
1. Read current pyproject.toml
2. Add claude-code-sdk to dependencies list
3. STOP - Alert user that dependencies changed
4. Wait for user confirmation before proceeding
5. After confirmation, dependencies are available
6. Document the change for future reference
```

## DATA
### Input:
- Current `pyproject.toml` content
- Dependency specification: `claude-code-sdk`

### Output:
- Updated `pyproject.toml` with new dependency
- Clean project structure ready for implementation

## Testing Strategy
⚠️ **IMPORTANT**: After adding dependency, tests requiring `claude-code-sdk` will fail until dependency is installed.

**Before dependency installation:**
- Run existing tests to ensure they still pass
- Verify project structure is correct

**After dependency installation (user confirms):**
- Verify project installs cleanly with new dependency
- Check that existing functionality still works
- Ensure no import conflicts
- Test that `import claude_code_sdk` works

## LLM Prompt for Implementation
```
I need to implement Step 1 of the LLM interface refactoring plan. Please:

1. Read the summary from pr_info/steps/summary.md to understand the overall goal
2. Add the claude-code-sdk dependency to pyproject.toml in the dependencies section
3. Ensure the dependency specification is compatible with Python 3.11+
4. ⚠️ STOP AFTER MODIFYING pyproject.toml - Alert me that dependencies have been updated
5. DO NOT proceed with any imports or tests that require the new dependency
6. Wait for my confirmation that I have installed the dependencies before continuing

**CRITICAL**: After adding the dependency, the system must stop and wait for user confirmation that dependencies are installed. Any code that imports claude_code_sdk will fail until then.
```
