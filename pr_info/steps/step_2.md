# Step 2: Create Commit Operations Module

## Objective
Create the commit operations module with structured parameter signature and move the commit function with comprehensive tests.

## WHERE
- **New File**: `src/mcp_coder/utils/commit_operations.py`
- **New Test File**: `tests/utils/test_commit_operations.py`

## WHAT
### Function to Move and Update
```python
# OLD signature (from CLI):
def generate_commit_message_with_llm(
    project_dir: Path, llm_method: str = "claude_code_api"
) -> Tuple[bool, str, Optional[str]]:

# NEW signature (in utils):
def generate_commit_message_with_llm(
    project_dir: Path, 
    provider: str = "claude", 
    method: str = "api"
) -> Tuple[bool, str, Optional[str]]:
```

### Test Functions to Create
```python
def test_generate_commit_message_with_llm_success_api()
def test_generate_commit_message_with_llm_success_cli()
def test_generate_commit_message_with_llm_staging_failure()
def test_generate_commit_message_with_llm_no_changes()
def test_generate_commit_message_with_llm_llm_failure()
def test_generate_commit_message_with_llm_invalid_provider()
```

## HOW
### Integration Points
```python
# Import dependencies (same logic as CLI implementation)
from ...constants import PROMPTS_FILE_PATH
from ...llm.interface import ask_llm
from ...prompt_manager import get_prompt
from ...utils.git_operations import (
    stage_all_changes,
    get_git_diff_for_commit
)
```

### Test Integration
```python
# Mock external dependencies in new location
@patch("mcp_coder.utils.commit_operations.stage_all_changes")
@patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
@patch("mcp_coder.utils.commit_operations.get_prompt")
@patch("mcp_coder.utils.commit_operations.ask_llm")
```

## ALGORITHM
```python
# Same logic, updated parameter handling:
1. Stage all changes using stage_all_changes()
2. Get git diff using get_git_diff_for_commit()
3. Load commit prompt template using get_prompt()
4. Call LLM with prompt using ask_llm() with provider, method
5. Parse and validate LLM response
6. Return (success, message, error) tuple
```

## DATA
### Input Parameters
- `project_dir: Path` - Project directory path
- `provider: str` - LLM provider ("claude")
- `method: str` - Communication method ("api" or "cli")

### Return Value
```python
Tuple[bool, str, Optional[str]]
# (success, commit_message, error_message)

# Success case:
(True, "feat: add new feature\n\nDetailed description", None)

# Error case:
(False, "", "No changes to commit. Ensure you have modified files...")
```

### Function Call Changes
```python
# Instead of calling parse_llm_method() internally:
# provider, method = parse_llm_method(llm_method)

# Function now receives structured parameters directly:
# ask_llm(prompt, provider=provider, method=method, timeout=timeout)
```

## LLM Prompt for Implementation

```
You are implementing Step 2 of the LLM parameter architecture improvement.

Reference the summary.md for full context. Your task is to:

1. Create `src/mcp_coder/utils/commit_operations.py` with the `generate_commit_message_with_llm()` function moved from CLI but with NEW signature using `provider, method` parameters.

2. Create comprehensive tests in `tests/utils/test_commit_operations.py` that cover:
   - Successful commit message generation with both API and CLI methods
   - Parameter validation for provider and method
   - Error cases: staging failure, no changes, LLM failure
   - Mock all external dependencies properly

The goal is to move the function with cleaner parameter interface. Follow TDD - write tests first, then implement.

Key requirements:
- Function signature uses `provider: str, method: str` instead of `llm_method: str`
- Same business logic as CLI version, just different parameter handling
- All imports and dependencies must work in new location
- Tests must verify provider/method parameters are passed to ask_llm()
- Error handling and return values must be identical to current implementation
```
