# Step 3: Refactor commands.py - Remove _get_coordinator usage and use direct imports

## LLM Prompt
```
You are implementing Issue #365: Refactor coordinator - Remove _get_coordinator() late-binding pattern.
See pr_info/steps/summary.md for full context.

This is Step 3: Remove `_get_coordinator` import from commands.py and replace all 
`coordinator.<func>()` calls with direct imports and calls.
```

## WHERE

### File to Modify
- `src/mcp_coder/cli/commands/coordinator/commands.py`

## WHAT

### Remove Import
```python
# DELETE _get_coordinator from this import
from .core import _get_coordinator, validate_repo_config

# KEEP only
from .core import validate_repo_config
```

### Add Direct Imports
```python
# ADD imports from user_config
from ....utils.user_config import (
    create_default_config,
    get_cache_refresh_minutes,
    get_config_file_path,
    load_config,
)

# ADD imports from core (functions defined there)
from .core import (
    dispatch_workflow,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)

# ADD imports from other modules (already partially imported, consolidate)
from ....utils.github_operations.issue_branch_manager import IssueBranchManager
from ....utils.github_operations.issue_cache import update_issue_labels_in_cache
from ....utils.github_operations.issue_manager import IssueManager
from ....utils.jenkins_operations.client import JenkinsClient
```

## HOW

### Replace Pattern in Functions

**Pattern to find and replace throughout the file:**
```python
# Before (appears in multiple functions)
coordinator = _get_coordinator()
coordinator.create_default_config()
coordinator.load_repo_config(...)
coordinator.get_jenkins_credentials()
coordinator.JenkinsClient(...)
coordinator.IssueManager(...)
coordinator.IssueBranchManager(...)
coordinator.get_cached_eligible_issues(...)
coordinator.get_eligible_issues(...)
coordinator.dispatch_workflow(...)
coordinator._update_issue_labels_in_cache(...)

# After
create_default_config()
load_repo_config(...)
get_jenkins_credentials()
JenkinsClient(...)
IssueManager(...)
IssueBranchManager(...)
get_cached_eligible_issues(...)
get_eligible_issues(...)
dispatch_workflow(...)
update_issue_labels_in_cache(...)  # Note: renamed, no underscore prefix
```

### Functions to Update
1. `execute_coordinator_test()` - uses coordinator pattern
2. `execute_coordinator_run()` - uses coordinator pattern
3. `_build_cached_issues_by_repo()` - uses coordinator pattern
4. `execute_coordinator_vscodeclaude()` - uses coordinator pattern
5. `_handle_intervention_mode()` - uses coordinator pattern

## ALGORITHM
```
1. Remove _get_coordinator from .core import
2. Add direct imports for all functions used via coordinator:
   - From user_config: create_default_config
   - From core: load_repo_config, get_jenkins_credentials, get_cached_eligible_issues, 
               get_eligible_issues, dispatch_workflow
   - From jenkins_operations.client: JenkinsClient
   - From issue_manager: IssueManager
   - From issue_branch_manager: IssueBranchManager
   - From issue_cache: update_issue_labels_in_cache
3. In each function:
   a. Delete "coordinator = _get_coordinator()" line
   b. Replace "coordinator.<func>" with "<func>" for each call
   c. Replace "coordinator._update_issue_labels_in_cache" with "update_issue_labels_in_cache"
4. Delete comments about late binding / test patching
```

## DATA

No data structure changes - only import and call patterns change.

## VERIFICATION

After this step:
```bash
# Should find 0 occurrences
grep "_get_coordinator" src/mcp_coder/cli/commands/coordinator/commands.py
grep "coordinator\." src/mcp_coder/cli/commands/coordinator/commands.py

# Should find direct function calls
grep "create_default_config()" src/mcp_coder/cli/commands/coordinator/commands.py
grep "JenkinsClient(" src/mcp_coder/cli/commands/coordinator/commands.py
```
