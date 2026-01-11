# Step 1: Move Source File to workflow_utils

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Move commit_operations.py from utils/ to workflow_utils/ and update its internal import for git_operations.
```

---

## WHERE: File Paths

| Action | Path |
|--------|------|
| DELETE | `src/mcp_coder/utils/commit_operations.py` |
| CREATE | `src/mcp_coder/workflow_utils/commit_operations.py` |

---

## WHAT: Changes Required

### 1. Copy file content to new location

Copy entire content of `src/mcp_coder/utils/commit_operations.py` to `src/mcp_coder/workflow_utils/commit_operations.py`.

### 2. Update one relative import

**Before** (line ~11 in the file):
```python
from .git_operations import get_git_diff_for_commit, stage_all_changes
```

**After**:
```python
from ..utils.git_operations import get_git_diff_for_commit, stage_all_changes
```

### 3. Delete original file

Delete `src/mcp_coder/utils/commit_operations.py`.

---

## HOW: Integration Points

All other imports in the file remain unchanged because they use `..` (parent) relative imports which work identically from both `utils/` and `workflow_utils/`:

```python
# These stay the same:
from ..constants import PROMPTS_FILE_PATH
from ..llm.env import prepare_llm_environment
from ..llm.interface import ask_llm
from ..llm.providers.claude.claude_code_api import ClaudeAPIError
from ..prompt_manager import get_prompt
```

---

## DATA: Functions Provided by Module

The module exports these functions (no changes to signatures):

| Function | Signature |
|----------|-----------|
| `strip_claude_footers` | `(message: str) -> str` |
| `generate_commit_message_with_llm` | `(project_dir: Path, provider: str = "claude", method: str = "api", execution_dir: Optional[str] = None) -> Tuple[bool, str, Optional[str]]` |
| `parse_llm_commit_response` | `(response: Optional[str]) -> Tuple[str, Optional[str]]` |

---

## Verification

After this step:
- File exists at `src/mcp_coder/workflow_utils/commit_operations.py`
- File deleted from `src/mcp_coder/utils/commit_operations.py`
- Import syntax is valid (can be checked with `python -c "from mcp_coder.workflow_utils.commit_operations import generate_commit_message_with_llm"`)

Note: Tests will fail until Step 2 and Step 3 are completed.
