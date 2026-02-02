# Issue #365: Refactor coordinator - Remove _get_coordinator() late-binding pattern

## Overview

Remove the `_get_coordinator()` late-binding pattern from the coordinator package and replace with direct imports. This simplifies the code by removing unnecessary indirection while maintaining testability through standard Python patching practices.

## Architectural / Design Changes

### Before (Current Pattern)
```
┌─────────────────────────────────────────────────────────────────┐
│ core.py / commands.py                                           │
│                                                                 │
│   def _get_coordinator() -> ModuleType:                         │
│       from mcp_coder.cli.commands import coordinator            │
│       return coordinator                                        │
│                                                                 │
│   # Usage:                                                      │
│   coordinator = _get_coordinator()                              │
│   coordinator.get_config_values(...)  # Late binding            │
│   coordinator.JenkinsClient(...)      # Late binding            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ __init__.py (re-exports for test patching)                      │
│                                                                 │
│   from ....utils.user_config import get_config_values           │
│   from ....utils.jenkins_operations.client import JenkinsClient │
│   # ... many re-exports for patching at package level           │
└─────────────────────────────────────────────────────────────────┘
```

### After (Direct Imports)
```
┌─────────────────────────────────────────────────────────────────┐
│ core.py                                                         │
│                                                                 │
│   from ....utils.user_config import get_config_values           │
│   from ....utils.github_operations.label_config import ...      │
│                                                                 │
│   # Usage:                                                      │
│   get_config_values(...)  # Direct call                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ commands.py                                                     │
│                                                                 │
│   from ....utils.user_config import create_default_config       │
│   from ....utils.jenkins_operations.client import JenkinsClient │
│   from .core import load_repo_config, get_jenkins_credentials   │
│                                                                 │
│   # Usage:                                                      │
│   create_default_config()  # Direct call                        │
│   JenkinsClient(...)       # Direct call                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ __init__.py (public API only, no test re-exports)               │
│                                                                 │
│   # Only public API exports                                     │
│   from .commands import execute_coordinator_run, ...            │
│   from .core import dispatch_workflow, get_eligible_issues, ... │
└─────────────────────────────────────────────────────────────────┘
```

### Test Patching Change
```
# Before: Patch at package level
@patch("mcp_coder.cli.commands.coordinator.get_config_values")

# After: Patch where imported (module-specific)
@patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
@patch("mcp_coder.cli.commands.coordinator.commands.JenkinsClient")
```

## Benefits

1. **Simpler code**: No indirection through `_get_coordinator()` function
2. **Explicit dependencies**: Imports clearly show what each module uses
3. **Standard practice**: Patching where used is modern Python convention
4. **Easier navigation**: IDE can follow imports directly

## Files to Modify

### Source Files
| File | Changes |
|------|---------|
| `src/mcp_coder/utils/github_operations/issue_cache.py` | Rename `_update_issue_labels_in_cache` → `update_issue_labels_in_cache` |
| `src/mcp_coder/cli/commands/coordinator/core.py` | Remove `_get_coordinator()`, add direct imports |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Remove `_get_coordinator` usage, add direct imports |
| `src/mcp_coder/cli/commands/coordinator/__init__.py` | Remove test-only re-exports, update renamed function |

### Test Files
| File | Changes |
|------|---------|
| `tests/cli/commands/coordinator/test_core.py` | Update patch locations to `...core.<name>` |
| `tests/cli/commands/coordinator/test_commands.py` | Update patch locations to `...commands.<name>` |

## Functions Being Refactored

### In `core.py` (2 functions to replace)
- `coordinator.get_config_values(...)` → `get_config_values(...)`
- `coordinator.load_labels_config(...)` → `load_labels_config(...)`

### In `commands.py` (11 functions to replace)
- `coordinator.create_default_config()` → `create_default_config()`
- `coordinator.load_repo_config(...)` → `load_repo_config(...)`
- `coordinator.get_jenkins_credentials()` → `get_jenkins_credentials()`
- `coordinator.JenkinsClient(...)` → `JenkinsClient(...)`
- `coordinator.IssueManager(...)` → `IssueManager(...)`
- `coordinator.IssueBranchManager(...)` → `IssueBranchManager(...)`
- `coordinator.get_cached_eligible_issues(...)` → `get_cached_eligible_issues(...)`
- `coordinator.get_eligible_issues(...)` → `get_eligible_issues(...)`
- `coordinator.dispatch_workflow(...)` → `dispatch_workflow(...)`
- `coordinator._update_issue_labels_in_cache(...)` → `update_issue_labels_in_cache(...)`

## Acceptance Criteria

- [ ] `_get_coordinator()` function removed from `core.py`
- [ ] All `coordinator = _get_coordinator()` patterns replaced with direct imports
- [ ] Tests updated to patch at correct module locations
- [ ] Test-only re-exports removed from `__init__.py`
- [ ] `_update_issue_labels_in_cache` renamed to `update_issue_labels_in_cache`
- [ ] All checks pass (pylint, mypy, pytest)
