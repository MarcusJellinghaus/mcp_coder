# Step 2: Implement Core Label Update Method in IssueManager

## Context
With test infrastructure in place (Step 1), we now implement the core functionality. This single method handles all label update logic following the KISS principle: one function, all responsibilities contained.

**Reference**: See `pr_info/steps/summary.md` for architectural overview.

## Objective
Implement `update_workflow_label()` method in `IssueManager` that passes all tests from Step 1. This method extracts issue numbers, validates relationships, looks up labels, and performs transitions - all non-blocking.

## WHERE: File Location
```
src/mcp_coder/utils/github_operations/issue_manager.py  (MODIFY)
  └─ Add update_workflow_label() method to IssueManager class
  └─ Add at end of class, before closing (around line 850)
```

## WHAT: Method Signature

```python
@log_function_call
def update_workflow_label(
    self,
    from_label_id: str,
    to_label_id: str,
    branch_name: Optional[str] = None,
) -> bool:
    """Update workflow label after successful workflow completion.
    
    This method handles complete label transition workflow:
    1. Extract issue number from branch name (or detect current branch)
    2. Verify branch is linked to the issue via GitHub API
    3. Look up actual label names from internal IDs
    4. Perform label transition (remove old, add new)
    
    Non-blocking: All errors are caught, logged, and return False.
    Workflow success is never affected by label update failures.
    
    Args:
        from_label_id: Internal ID of source label (e.g., "implementing")
        to_label_id: Internal ID of target label (e.g., "code_review")
        branch_name: Optional branch name. If None, detects current branch.
    
    Returns:
        True if label updated successfully, False otherwise
        
    Example:
        >>> manager = IssueManager(project_dir)
        >>> success = manager.update_workflow_label("implementing", "code_review")
        >>> if success:
        ...     print("Label updated")
    """
```

## HOW: Integration Points

### Required Imports (add to top of file)
```python
import re  # For regex pattern matching
from typing import Optional  # Already imported, verify present
from mcp_coder.utils.git_operations.branches import get_current_branch_name
from mcp_coder.utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
    build_label_lookups,
)
from mcp_coder.utils.github_operations.issue_branch_manager import IssueBranchManager
```

### Decorators
```python
@log_function_call  # Already used in class, consistent pattern
# Note: Do NOT use @_handle_github_errors here - we need custom error handling
```

### Method Location
Place after `set_labels()` method, before end of `IssueManager` class.

## ALGORITHM: Core Logic Flow

```pseudocode
1. Get branch name (provided or auto-detect via git)
2. Extract issue_number from branch using regex ^(\d+)-
   → If no match: log WARNING, return False
   
3. Verify branch is linked to issue:
   → branch_manager.get_linked_branches(issue_number)
   → If branch not in list: log WARNING, return False
   
4. Load label config and build lookups:
   → get_labels_config_path(project_dir)
   → load_labels_config(path)
   → build_label_lookups(config)
   
5. Lookup actual label names from internal IDs:
   → from_label_name = lookups["id_to_name"].get(from_label_id)
   → to_label_name = lookups["id_to_name"].get(to_label_id)
   → If either None: log ERROR, return False
   
6. Get current issue labels:
   → issue_data = self.get_issue(issue_number)
   → If issue_data["number"] == 0: log ERROR, return False
   → current_labels = set(issue_data["labels"])
   
7. Check if already in target state (idempotent):
   → If to_label_name in current_labels and from_label_name not in current_labels:
      log DEBUG, return True (already done)
   
8. Compute new label set:
   → new_labels = current_labels - {from_label_name} | {to_label_name}
   
9. Apply label transition:
   → result = self.set_labels(issue_number, *new_labels)
   → If result["number"] == 0: log ERROR, return False
   → log INFO success, return True

WRAP ALL IN try/except:
   → Catch all exceptions
   → Log ERROR with details
   → Return False
```

## DATA: Internal Data Structures

### Branch Name Regex Pattern
```python
BRANCH_PATTERN = r'^(\d+)-'
# Matches: "123-feature-name" → group(1) = "123"
# Doesn't match: "feature-123", "main", "develop"
```

### Label Lookups (from build_label_lookups)
```python
{
    "id_to_name": {
        "implementing": "status-06:implementing",
        "code_review": "status-07:code-review",
        ...
    },
    "all_names": {...},
    "name_to_category": {...},
    "name_to_id": {...}
}
```

### Return Value
```python
bool: True if successful, False on any error
# Always returns, never raises exceptions
```

## Implementation Details

### Error Handling Pattern
```python
try:
    # Main logic here
    
    # Example error case
    if not from_label_name:
        logger.error(
            f"Label ID '{from_label_id}' not found in configuration. "
            f"Available IDs: {list(label_lookups['id_to_name'].keys())}"
        )
        return False
    
    # More logic...
    
except Exception as e:
    logger.error(f"Unexpected error updating workflow label: {e}")
    return False
```

### Logging Levels Guide
```python
# INFO: Successful operations
logger.info(f"Successfully updated issue #{issue_number} label: "
           f"{from_label_name} → {to_label_name}")

# DEBUG: Skipped operations (idempotent, flag not passed, etc.)
logger.debug(f"Issue #{issue_number} already has label '{to_label_name}', skipping")

# WARNING: Expected failures (branch pattern, not linked, etc.)
logger.warning(f"Branch '{branch_name}' does not follow {issue_number}-title pattern")

# ERROR: Unexpected failures (API errors, missing config, etc.)
logger.error(f"Failed to get issue #{issue_number}: {error_details}")
```

### Branch-Issue Verification
```python
# Use existing IssueBranchManager
branch_manager = IssueBranchManager(
    project_dir=self._project_dir,
    repo_url=self._repo_url
)
linked_branches = branch_manager.get_linked_branches(issue_number)

if branch_name not in linked_branches:
    logger.warning(
        f"Branch '{branch_name}' is not linked to issue #{issue_number}. "
        f"Linked branches: {linked_branches}"
    )
    return False
```

### Idempotent Check
```python
# Check if already in target state
if to_label_name in current_labels:
    if from_label_name not in current_labels:
        # Already transitioned, nothing to do
        logger.debug(
            f"Issue #{issue_number} already has label '{to_label_name}' "
            f"without '{from_label_name}'. No action needed."
        )
        return True
    # else: Has both labels, proceed with removal of old label
```

## Validation Checklist
- [ ] Method signature matches specification exactly
- [ ] All imports added to top of file
- [ ] `@log_function_call` decorator applied
- [ ] Complete docstring with Args, Returns, Example
- [ ] Branch name regex extracts issue number correctly
- [ ] Branch-issue verification via `get_linked_branches()`
- [ ] Label config loading with proper error handling
- [ ] Idempotent behavior (checks current state)
- [ ] All error cases return False (never raise)
- [ ] Appropriate logging at all levels (INFO/DEBUG/WARNING/ERROR)
- [ ] Uses existing `self.get_issue()` and `self.set_labels()`
- [ ] No GitHub API calls outside existing methods
- [ ] All Step 1 tests pass

## Testing Commands
```bash
# Run only the new label update tests
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-v", "tests/utils/github_operations/test_issue_manager_label_update.py"]
)

# Run all IssueManager tests to ensure no regression
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-v", "tests/utils/github_operations/test_issue_manager.py"]
)

# Type checking
mcp__code-checker__run_mypy_check()

# Code quality
mcp__code-checker__run_pylint_check()
```

## Next Step Preview
**Step 3** will add CLI flags to the argument parsers, enabling users to opt-in to label updates.

---

## LLM Prompt for This Step

```
You are implementing Step 2 of the auto-label update feature for mcp-coder.

CONTEXT:
Read pr_info/steps/summary.md for architectural overview.
Step 1 created test infrastructure - now implement the actual functionality.

TASK:
Add update_workflow_label() method to IssueManager class in:
src/mcp_coder/utils/github_operations/issue_manager.py

METHOD REQUIREMENTS:
1. Extract issue number from branch name using regex ^(\d+)-
2. Verify branch is linked via IssueBranchManager.get_linked_branches()
3. Load label config and lookup actual label names from internal IDs
4. Check if already in target state (idempotent)
5. Perform label transition using existing set_labels() method
6. Non-blocking: catch all exceptions, return False on any error
7. Comprehensive logging (INFO/DEBUG/WARNING/ERROR)

INTEGRATION:
- Use @log_function_call decorator (existing pattern)
- Use existing methods: get_issue(), set_labels()
- Use existing IssueBranchManager for verification
- Use label_config functions for lookups
- Follow existing error handling patterns in the class

VALIDATION:
All tests from Step 1 must pass after implementation.

REFERENCE THIS STEP:
pr_info/steps/step_2.md (contains detailed algorithm and specifications)

After implementation, run code quality checks:
1. mcp__code-checker__run_pytest_check focusing on label_update tests
2. mcp__code-checker__run_mypy_check
3. mcp__code-checker__run_pylint_check
```
