# Step 1: Create Commit Operations Module and Tests

## Objective
Create the new `utils/commit_operations.py` module and comprehensive tests following TDD principles.

## WHERE
- **New File**: `src/mcp_coder/utils/commit_operations.py`
- **New Test File**: `tests/utils/test_commit_operations.py`

## WHAT
### Main Function to Move
```python
def generate_commit_message_with_llm(
    project_dir: Path, 
    llm_method: str = "claude_code_api"
) -> Tuple[bool, str, Optional[str]]:
    """Generate commit message using LLM. 
    
    Returns (success, message, error).
    """
```

### Test Functions to Create
```python
def test_generate_commit_message_with_llm_success()
def test_generate_commit_message_with_llm_respects_llm_method()
def test_generate_commit_message_with_llm_staging_failure()
def test_generate_commit_message_with_llm_no_changes()
def test_generate_commit_message_with_llm_llm_failure()
```

## HOW
### Integration Points
```python
# Import dependencies (same as current implementation)
from ...constants import PROMPTS_FILE_PATH
from ...llm.interface import ask_llm
from ...llm.session import parse_llm_method
from ...prompt_manager import get_prompt
from ...utils.git_operations import (
    stage_all_changes,
    get_git_diff_for_commit
)
```

### Test Integration
```python
# Mock the same external dependencies
@patch("mcp_coder.utils.commit_operations.stage_all_changes")
@patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
@patch("mcp_coder.utils.commit_operations.get_prompt")
@patch("mcp_coder.utils.commit_operations.ask_llm")
```

## ALGORITHM
```python
# Core logic (unchanged from current implementation):
1. Stage all changes using stage_all_changes()
2. Get git diff using get_git_diff_for_commit()
3. Load commit prompt template using get_prompt()
4. Call LLM with prompt using ask_llm() and llm_method
5. Parse and validate LLM response
6. Return (success, message, error) tuple
```

## DATA
### Input Parameters
- `project_dir: Path` - Project directory path
- `llm_method: str` - LLM method ("claude_code_cli" or "claude_code_api")

### Return Value
```python
Tuple[bool, str, Optional[str]]
# (success, commit_message, error_message)

# Success case:
(True, "feat: add new feature\n\nDetailed description", None)

# Error case:
(False, "", "No changes to commit. Ensure you have modified files...")
```

### Test Data Structures
```python
# Mock return values for testing
MOCK_GIT_DIFF = "diff --git a/file.py b/file.py\n+new line"
MOCK_PROMPT = "Generate commit message for changes"
MOCK_LLM_RESPONSE = "feat: add new feature"
```

## LLM Prompt for Implementation

```
You are implementing Step 1 of the commit auto function architecture fix. 

Reference the summary.md for full context. Your task is to:

1. Create `src/mcp_coder/utils/commit_operations.py` with the `generate_commit_message_with_llm()` function moved from `src/mcp_coder/cli/commands/commit.py`. Keep the EXACT same implementation - just move it.

2. Create comprehensive tests in `tests/utils/test_commit_operations.py` that cover:
   - Successful commit message generation
   - llm_method parameter is actually used (not ignored)
   - Error cases: staging failure, no changes, LLM failure
   - Mock all external dependencies properly

The goal is to move the function without changing behavior, but ensure it's properly tested in its new location. Follow TDD - write tests first, then move the function.

Key requirements:
- Function signature must remain identical for backward compatibility
- All imports and dependencies must work in new location
- Tests must verify llm_method parameter is passed to ask_llm()
- Error handling and return values must be identical to current implementation
```
