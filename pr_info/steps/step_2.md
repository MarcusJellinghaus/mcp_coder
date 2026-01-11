# Step 2: Move Test File to tests/workflow_utils

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Move test_commit_operations.py from tests/utils/ to tests/workflow_utils/ and update all import paths and mock decorators.
```

---

## WHERE: File Paths

| Action | Path |
|--------|------|
| DELETE | `tests/utils/test_commit_operations.py` |
| CREATE | `tests/workflow_utils/test_commit_operations.py` |

---

## WHAT: Changes Required

### 1. Copy file content to new location

Copy entire content of `tests/utils/test_commit_operations.py` to `tests/workflow_utils/test_commit_operations.py`.

### 2. Update import statements

**Before**:
```python
from mcp_coder.utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
    strip_claude_footers,
)
```

**After**:
```python
from mcp_coder.workflow_utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
    strip_claude_footers,
)
```

### 3. Update ALL mock patch decorators

Find and replace all occurrences of mock paths:

| Before | After |
|--------|-------|
| `@patch("mcp_coder.utils.commit_operations.prepare_llm_environment")` | `@patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")` |
| `@patch("mcp_coder.utils.commit_operations.stage_all_changes")` | `@patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")` |
| `@patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")` | `@patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")` |
| `@patch("mcp_coder.utils.commit_operations.get_prompt")` | `@patch("mcp_coder.workflow_utils.commit_operations.get_prompt")` |
| `@patch("mcp_coder.utils.commit_operations.ask_llm")` | `@patch("mcp_coder.workflow_utils.commit_operations.ask_llm")` |
| `@patch("mcp_coder.utils.commit_operations.parse_llm_commit_response")` | `@patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")` |

**Simple approach**: Global find-replace `mcp_coder.utils.commit_operations` → `mcp_coder.workflow_utils.commit_operations`

### 4. Delete original file

Delete `tests/utils/test_commit_operations.py`.

---

## HOW: Pattern for Updates

The test file uses these import patterns that need updating:

```python
# Direct imports (update path)
from mcp_coder.workflow_utils.commit_operations import (...)

# Mock patches (update all occurrences)
@patch("mcp_coder.workflow_utils.commit_operations.<function_name>")
```

---

## DATA: Test Classes in File

| Class | Tests |
|-------|-------|
| `TestGenerateCommitMessageWithLLM` | 18 test methods |
| `TestParseLLMCommitResponse` | 1 test method |
| `TestStripClaudeFooters` | 12 test methods |

---

## Verification

After this step:
- File exists at `tests/workflow_utils/test_commit_operations.py`
- File deleted from `tests/utils/test_commit_operations.py`
- No references to `mcp_coder.utils.commit_operations` in the test file
- Can run: `pytest tests/workflow_utils/test_commit_operations.py -v` (should pass after Step 1 is complete)
