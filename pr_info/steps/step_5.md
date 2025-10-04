# Step 5: Update Workflow Layer

## Objective
Update the workflow layer to use structured parameter signatures and fix the architectural violation.

## WHERE
- **Modify**: `src/mcp_coder/workflows/implement/core.py`
- **Modify**: `src/mcp_coder/workflows/implement/task_processing.py`
- **Modify**: `src/mcp_coder/cli/commands/implement.py`

## WHAT
### Function Signatures to Update
```python
# workflows/implement/core.py
# Before:
def run_implement_workflow(project_dir: Path, llm_method: str) -> int:

# After:
def run_implement_workflow(project_dir: Path, provider: str, method: str) -> int:
```

```python
# workflows/implement/task_processing.py
# Before:
def process_single_task(project_dir: Path, llm_method: str) -> tuple[bool, str]:
def commit_changes(project_dir: Path) -> bool:

# After:
def process_single_task(project_dir: Path, provider: str, method: str) -> tuple[bool, str]:
def commit_changes(project_dir: Path, provider: str, method: str) -> bool:
```

### Import to Fix
```python
# workflows/implement/task_processing.py
# OLD (importing from CLI - VIOLATION):
from mcp_coder.cli.commands.commit import generate_commit_message_with_llm

# NEW (importing from utils - CORRECT):
from mcp_coder.utils.commit_operations import generate_commit_message_with_llm
```

### CLI Command Update
```python
# cli/commands/implement.py
# Before:
def execute_implement(args: argparse.Namespace) -> int:
    return run_implement_workflow(project_dir, args.llm_method)

# After:
def execute_implement(args: argparse.Namespace) -> int:
    provider, method = parse_llm_method_from_args(args.llm_method)
    return run_implement_workflow(project_dir, provider, method)
```

## HOW
### Integration Points
```python
# cli/commands/implement.py - Add import and update call
from ..utils import parse_llm_method_from_args

def execute_implement(args: argparse.Namespace) -> int:
    provider, method = parse_llm_method_from_args(args.llm_method)
    return run_implement_workflow(project_dir, provider, method)

# workflows/implement/core.py - Update signature and pass parameters
def run_implement_workflow(project_dir: Path, provider: str, method: str) -> int:
    success, reason = process_single_task(project_dir, provider, method)

# workflows/implement/task_processing.py - Fix import and signatures
from mcp_coder.utils.commit_operations import generate_commit_message_with_llm

def process_single_task(project_dir: Path, provider: str, method: str) -> tuple[bool, str]:
    if not commit_changes(project_dir, provider, method):
        return False, "error"

def commit_changes(project_dir: Path, provider: str, method: str) -> bool:
    success, commit_message, error = generate_commit_message_with_llm(project_dir, provider, method)
```

### Parameter Flow Fix
```python
# Complete parameter flow:
CLI: args.llm_method 
  ↓ parse_llm_method_from_args()
(provider, method)
  ↓ run_implement_workflow(project_dir, provider, method)
  ↓ process_single_task(project_dir, provider, method)
  ↓ commit_changes(project_dir, provider, method)
  ↓ generate_commit_message_with_llm(project_dir, provider, method)
```

## ALGORITHM
```python
# Workflow layer update process:
1. Update cli/commands/implement.py to use shared utility and pass structured parameters
2. Update workflows/implement/core.py function signature and parameter passing
3. Update workflows/implement/task_processing.py import and function signatures
4. Remove all internal parse_llm_method() calls from workflow files
5. Verify parameter flow works end-to-end
6. Update any relevant tests
```

## DATA
### Function Signature Changes
```python
# 4 functions need signature updates:
1. run_implement_workflow(project_dir, provider, method)
2. process_single_task(project_dir, provider, method) 
3. commit_changes(project_dir, provider, method)
4. execute_implement(args) - internal logic change only
```

### Import Changes
```python
# cli/commands/implement.py:
+ from ..utils import parse_llm_method_from_args

# workflows/implement/task_processing.py:
- from mcp_coder.cli.commands.commit import generate_commit_message_with_llm
+ from mcp_coder.utils.commit_operations import generate_commit_message_with_llm

# Remove internal parsing from workflows:
- from mcp_coder.llm.session import parse_llm_method (if present)
```

### Parameter Threading
```python
# All these functions now receive structured parameters directly:
def _call_llm_with_comprehensive_capture(prompt: str, provider: str, method: str):
def check_and_fix_mypy(project_dir: Path, step_num: int, provider: str, method: str):

# No more internal parameter parsing in workflow layer
```

## LLM Prompt for Implementation

```
You are implementing Step 5 of the LLM parameter architecture improvement.

Reference the summary.md for full context. Your task is to update the workflow layer to use structured parameters and fix the architectural violation:

1. Update `src/mcp_coder/cli/commands/implement.py`:
   - Add: `from ..utils import parse_llm_method_from_args`
   - Update `execute_implement()` to parse parameters and pass them as structured args

2. Update `src/mcp_coder/workflows/implement/core.py`:
   - Change `run_implement_workflow()` signature to use `provider: str, method: str`
   - Pass structured parameters to `process_single_task()`

3. Update `src/mcp_coder/workflows/implement/task_processing.py`:
   - Fix import violation: import from utils instead of CLI
   - Update `process_single_task()` and `commit_changes()` signatures
   - Update any other functions that handle LLM parameters
   - Remove internal `parse_llm_method()` calls

This fixes the architectural violation (workflows importing CLI) and creates consistent parameter handling throughout the system.

Key requirements:
- Remove CLI import, add utils import in task_processing.py
- Update all function signatures to use provider, method parameters
- Thread structured parameters through the entire call chain
- Remove all internal LLM parameter parsing from workflow layer
- All existing functionality must work identically
```
