# Step 2: Add Branch Name to All LLM Call Sites

## Objective

Update all LLM call sites to pass `branch_name` parameter for better log file correlation. When branch name is unavailable but issue_id is known, use `{issue_id}-issue` format.

## Prerequisites

- Step 0 completed (stream logging with branch_name parameter)
- Step 1 completed (test file refactoring)

## WHERE: File Paths

**New utility function:**
- `src/mcp_coder/utils/git_utils.py` (add function if file exists, or create)

**Files to update (13 call sites across 6 files):**
- `src/mcp_coder/workflows/implement/core.py` (4 calls)
- `src/mcp_coder/workflows/implement/task_processing.py` (2 calls)
- `src/mcp_coder/workflows/create_plan.py` (3 calls)
- `src/mcp_coder/workflows/create_pr/core.py` (1 call)
- `src/mcp_coder/workflow_utils/commit_operations.py` (1 call)
- `src/mcp_coder/cli/commands/prompt.py` (2 calls)

**Test files:**
- `tests/utils/test_git_utils.py` (add tests for new function)

## WHAT: Main Functions

### New Utility Function

```python
# src/mcp_coder/utils/git_utils.py

def get_branch_name_for_logging(
    project_dir: str | Path | None = None,
    issue_id: str | int | None = None,
) -> str | None:
    """Get branch name for LLM log file naming.
    
    Args:
        project_dir: Directory to get git branch from
        issue_id: Fallback issue ID if branch unavailable
        
    Returns:
        Branch name, "{issue_id}-issue" fallback, or None
    """
```

### Updated Call Sites

Each call site needs to:
1. Determine available context (project_dir, issue_id)
2. Call `get_branch_name_for_logging()` 
3. Pass result as `branch_name` parameter to LLM function

## HOW: Integration Points

### Pattern for Workflow Files

```python
from mcp_coder.utils.git_utils import get_branch_name_for_logging

# Before LLM call
branch_name = get_branch_name_for_logging(
    project_dir=config.project_dir,  # or project_dir variable
    issue_id=issue_number,  # if available, else None
)

# LLM call
response = ask_llm(
    prompt,
    # ... existing params ...
    branch_name=branch_name,  # Add this
)
```

## ALGORITHM: Utility Function Logic

```python
def get_branch_name_for_logging(project_dir, issue_id):
    if project_dir:
        branch = get_current_branch(project_dir)  # existing function
        if branch and branch != "HEAD":
            return branch
    
    if issue_id:
        return f"{issue_id}-issue"
    
    return None
```

## DATA: Call Site Details

| File | Function | Line | Has project_dir | Has issue_id |
|------|----------|------|-----------------|--------------|
| implement/core.py | _run_ci_analysis | 155 | config.project_dir | No |
| implement/core.py | _run_ci_fix | 223 | config.project_dir | No |
| implement/core.py | prepare_task_tracker | 682 | project_dir | No |
| implement/core.py | run_finalisation | 852 | project_dir | No |
| implement/task_processing.py | _call_llm_with_comprehensive_capture | 136,178 | cwd | No |
| create_plan.py | run_planning_prompts | 322,374,420 | project_dir | issue_number |
| create_pr/core.py | generate_pr_summary | 301 | execution_dir | No |
| commit_operations.py | generate_commit_message_with_llm | 150 | project_dir | No |
| cli/commands/prompt.py | execute_prompt | 160,176 | project_dir | No |

## Verification

```bash
# Run unit tests for new utility
pytest tests/utils/test_git_utils.py -v -k "branch_name_for_logging"

# Run affected workflow tests
pytest tests/workflows/ -v

# Run full test suite
mcp__code-checker__run_pytest_check
```

## LLM Prompt for This Step

```
Read the summary at pr_info/steps/summary.md and this step file.

Implement branch_name propagation to all LLM call sites:

1. First, add a utility function to src/mcp_coder/utils/git_utils.py:
   - get_branch_name_for_logging(project_dir, issue_id) -> str | None
   - Returns current git branch if available
   - Falls back to "{issue_id}-issue" if branch unavailable but issue_id provided
   - Returns None if neither available
   - Add tests in tests/utils/test_git_utils.py

2. Update each call site listed in the step file to:
   - Import get_branch_name_for_logging
   - Get branch_name using available context (project_dir, issue_id)
   - Pass branch_name to ask_llm/prompt_llm calls

3. Run mcp__code-checker__run_pytest_check to verify all tests pass

Note: create_plan.py has issue_number parameter available - use it as fallback.
Other files only have project_dir - branch detection only.
```
