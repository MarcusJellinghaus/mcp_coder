# Step 4: Update coordinator __init__.py - Remove test-only re-exports

## LLM Prompt
```
You are implementing Issue #365: Refactor coordinator - Remove _get_coordinator() late-binding pattern.
See pr_info/steps/summary.md for full context.

This is Step 4: Update the coordinator package's __init__.py to remove test-only re-exports
and update the renamed function export.
```

## WHERE

### File to Modify
- `src/mcp_coder/cli/commands/coordinator/__init__.py`

## WHAT

### Identify Test-Only Re-exports to Remove

These imports exist solely to enable patching at `mcp_coder.cli.commands.coordinator.<name>`:

```python
# REMOVE these test-only re-exports
from ....utils.github_operations.issue_branch_manager import IssueBranchManager
from ....utils.github_operations.issue_cache import (
    CacheData,
    _update_issue_labels_in_cache,  # Also renamed
)
from ....utils.github_operations.issue_manager import IssueManager
from ....utils.github_operations.label_config import load_labels_config
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.user_config import create_default_config, get_config_values
```

### Keep Public API Exports

```python
# KEEP these - they are the public API
from .command_templates import (
    CREATE_PLAN_COMMAND_TEMPLATE,
    CREATE_PLAN_COMMAND_WINDOWS,
    CREATE_PR_COMMAND_TEMPLATE,
    CREATE_PR_COMMAND_WINDOWS,
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
    IMPLEMENT_COMMAND_TEMPLATE,
    IMPLEMENT_COMMAND_WINDOWS,
    PRIORITY_ORDER,
    TEST_COMMAND_TEMPLATES,
)

from .commands import (
    execute_coordinator_run,
    execute_coordinator_test,
    execute_coordinator_vscodeclaude,
    execute_coordinator_vscodeclaude_status,
    format_job_output,
)

from .core import (
    _filter_eligible_issues,
    dispatch_workflow,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)

from .workflow_constants import WORKFLOW_MAPPING
```

### Update __all__ List

```python
# REMOVE from __all__:
# - "CacheData" (if only used for testing)
# - "_update_issue_labels_in_cache" 
# - "create_default_config"
# - "get_config_values"
# - "load_labels_config"
# - "JenkinsClient"
# - "IssueManager"
# - "IssueBranchManager"

# The __all__ should only contain:
__all__ = [
    # Public CLI interface
    "execute_coordinator_test",
    "execute_coordinator_run",
    "execute_coordinator_vscodeclaude",
    "execute_coordinator_vscodeclaude_status",
    "format_job_output",
    # Public business logic
    "dispatch_workflow",
    "get_cached_eligible_issues",
    "get_eligible_issues",
    "load_repo_config",
    "validate_repo_config",
    "get_jenkins_credentials",
    # Constants and templates
    "DEFAULT_TEST_COMMAND",
    "DEFAULT_TEST_COMMAND_WINDOWS",
    "CREATE_PLAN_COMMAND_WINDOWS",
    "IMPLEMENT_COMMAND_WINDOWS",
    "CREATE_PR_COMMAND_WINDOWS",
    "TEST_COMMAND_TEMPLATES",
    "CREATE_PLAN_COMMAND_TEMPLATE",
    "IMPLEMENT_COMMAND_TEMPLATE",
    "CREATE_PR_COMMAND_TEMPLATE",
    "PRIORITY_ORDER",
    "WORKFLOW_MAPPING",
    # Internal (kept for compatibility if needed)
    "_filter_eligible_issues",
]
```

## HOW

1. Remove import statements for test-only re-exports
2. Update `__all__` to remove test-only exports
3. Remove any comments about "test patching support"

## ALGORITHM
```
1. Delete import lines for: IssueBranchManager, IssueManager, JenkinsClient,
   create_default_config, get_config_values, load_labels_config, CacheData,
   _update_issue_labels_in_cache
2. Update __all__ to remove those names
3. Remove comments mentioning "test patching" or "for testing"
```

## DATA

No data structure changes.

## VERIFICATION

After this step:
```bash
# Should NOT find these in __init__.py
grep "JenkinsClient" src/mcp_coder/cli/commands/coordinator/__init__.py
grep "IssueManager" src/mcp_coder/cli/commands/coordinator/__init__.py
grep "create_default_config" src/mcp_coder/cli/commands/coordinator/__init__.py
grep "_update_issue_labels_in_cache" src/mcp_coder/cli/commands/coordinator/__init__.py

# Should still export public API
grep "execute_coordinator_run" src/mcp_coder/cli/commands/coordinator/__init__.py
grep "dispatch_workflow" src/mcp_coder/cli/commands/coordinator/__init__.py
```
