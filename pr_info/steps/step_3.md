# Step 3: Update Imports in Dependent Files

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Update import paths in three files that depend on commit_operations: commit.py, task_processing.py, and test_commit.py.
```

---

## WHERE: Files to Modify

| File | Type |
|------|------|
| `src/mcp_coder/cli/commands/commit.py` | Source |
| `src/mcp_coder/workflows/implement/task_processing.py` | Source |
| `tests/cli/commands/test_commit.py` | Test |

---

## WHAT: Changes Required

### File 1: `src/mcp_coder/cli/commands/commit.py`

**Before** (around line 12):
```python
from ...utils.commit_operations import generate_commit_message_with_llm
```

**After**:
```python
from ...workflow_utils.commit_operations import generate_commit_message_with_llm
```

---

### File 2: `src/mcp_coder/workflows/implement/task_processing.py`

**Before** (around line 20):
```python
from mcp_coder.utils.commit_operations import generate_commit_message_with_llm
```

**After**:
```python
from mcp_coder.workflow_utils.commit_operations import generate_commit_message_with_llm
```

---

### File 3: `tests/cli/commands/test_commit.py`

#### 3a. Update direct import

**Before** (around line 14):
```python
from mcp_coder.utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
)
```

**After**:
```python
from mcp_coder.workflow_utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
)
```

#### 3b. Update mock patch decorators

Find and replace all mock paths in this file:

| Before | After |
|--------|-------|
| `@patch("mcp_coder.utils.commit_operations.stage_all_changes")` | `@patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")` |
| `@patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")` | `@patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")` |
| `@patch("mcp_coder.utils.commit_operations.get_prompt")` | `@patch("mcp_coder.workflow_utils.commit_operations.get_prompt")` |
| `@patch("mcp_coder.utils.commit_operations.ask_llm")` | `@patch("mcp_coder.workflow_utils.commit_operations.ask_llm")` |
| `@patch("mcp_coder.utils.commit_operations.parse_llm_commit_response")` | `@patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")` |

**Simple approach**: Global find-replace `mcp_coder.utils.commit_operations` → `mcp_coder.workflow_utils.commit_operations`

---

## HOW: Verification Commands

After making changes, verify imports are correct:

```bash
# Check source files import correctly
python -c "from mcp_coder.cli.commands.commit import execute_commit_auto"
python -c "from mcp_coder.workflows.implement.task_processing import commit_changes"

# Check test file imports correctly
python -c "from tests.cli.commands.test_commit import TestExecuteCommitAuto"
```

---

## DATA: Import Patterns Used

| File | Import Style |
|------|--------------|
| `commit.py` | Relative: `from ...workflow_utils.commit_operations` |
| `task_processing.py` | Absolute: `from mcp_coder.workflow_utils.commit_operations` |
| `test_commit.py` | Absolute: `from mcp_coder.workflow_utils.commit_operations` |

---

## Verification

After this step:
- No references to `utils.commit_operations` in any of the three files
- All imports resolve correctly
- Ready for final test verification in Step 4
