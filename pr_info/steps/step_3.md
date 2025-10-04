# Step 3: Fix Workflow Import and Parameter Threading

## Objective
Update the implement workflow to import from utils (not CLI) and pass the `llm_method` parameter correctly.

## WHERE
- **Modify**: `src/mcp_coder/workflows/implement/task_processing.py`
- **Function**: `commit_changes()` around line 545

## WHAT
### Import to Change
```python
# OLD (importing from CLI - VIOLATION):
from mcp_coder.cli.commands.commit import generate_commit_message_with_llm

# NEW (importing from utils - CORRECT):
from mcp_coder.utils.commit_operations import generate_commit_message_with_llm
```

### Function Call to Fix
```python
# OLD (missing llm_method parameter):
def commit_changes(project_dir: Path) -> bool:
    success, commit_message, error = generate_commit_message_with_llm(project_dir)

# NEW (passing llm_method parameter):
def commit_changes(project_dir: Path, llm_method: str = "claude_code_api") -> bool:
    success, commit_message, error = generate_commit_message_with_llm(project_dir, llm_method)
```

### Caller to Update
```python
# Function that calls commit_changes() - around line 500+
def process_single_task(project_dir: Path, llm_method: str) -> tuple[bool, str]:
    # Update this call:
    if not commit_changes(project_dir, llm_method):  # Pass llm_method
        return False, "error"
```

## HOW
### Integration Points
```python
# Update import at top of file
from mcp_coder.utils.commit_operations import generate_commit_message_with_llm

# Update function signature
def commit_changes(project_dir: Path, llm_method: str = "claude_code_api") -> bool:

# Update function call in process_single_task()
if not commit_changes(project_dir, llm_method):
```

### Threading llm_method Parameter
```python
# Parameter flow:
process_single_task(project_dir, llm_method)
    ↓ passes llm_method to
commit_changes(project_dir, llm_method) 
    ↓ passes llm_method to
generate_commit_message_with_llm(project_dir, llm_method)
```

## ALGORITHM
```python
# Parameter threading fix:
1. Add llm_method parameter to commit_changes() signature
2. Pass llm_method from process_single_task() to commit_changes()
3. Pass llm_method from commit_changes() to generate_commit_message_with_llm()
4. Update import from CLI to utils
5. Verify parameter flows correctly through call chain
```

## DATA
### Function Signatures
```python
# Before:
def commit_changes(project_dir: Path) -> bool:

# After:
def commit_changes(project_dir: Path, llm_method: str = "claude_code_api") -> bool:
```

### Function Calls
```python
# In process_single_task():
# Before:
if not commit_changes(project_dir):

# After:  
if not commit_changes(project_dir, llm_method):
```

### Import Changes
```python
# Remove:
from mcp_coder.cli.commands.commit import generate_commit_message_with_llm

# Add:
from mcp_coder.utils.commit_operations import generate_commit_message_with_llm
```

## LLM Prompt for Implementation

```
You are implementing Step 3 of the commit auto function architecture fix.

Reference the summary.md for full context. Your task is to fix the workflow import violation and parameter threading in `src/mcp_coder/workflows/implement/task_processing.py`:

1. Change the import from CLI to utils:
   - Remove: `from mcp_coder.cli.commands.commit import generate_commit_message_with_llm`
   - Add: `from mcp_coder.utils.commit_operations import generate_commit_message_with_llm`

2. Fix the `commit_changes()` function to accept and pass `llm_method`:
   - Add `llm_method: str = "claude_code_api"` parameter
   - Pass it to `generate_commit_message_with_llm(project_dir, llm_method)`

3. Update the caller `process_single_task()` to pass `llm_method`:
   - Change `commit_changes(project_dir)` to `commit_changes(project_dir, llm_method)`

This fixes the architectural violation (workflows importing CLI) and ensures the user's chosen LLM method is respected in workflows.

Key requirements:
- Remove CLI import, add utils import
- Thread llm_method parameter through the call chain
- Maintain backward compatibility with default parameter
- No other behavior changes
```
