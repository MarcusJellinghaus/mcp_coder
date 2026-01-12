# Issue #277: Refactor utils/__init__.py Import Dependencies

## Overview

This refactoring fixes an architectural violation where `github_operations` has an unintended transitive dependency on `jenkins_operations` through the `utils/__init__.py` facade.

## Problem

```
github_operations/pr_manager.py 
    → imports from mcp_coder.utils 
    → utils/__init__.py loads ALL submodules including jenkins_operations
    → Violates "External Service Integrations Independence" contract
```

## Solution

Change internal submodule imports to use direct sibling imports instead of going through the parent package facade.

## Architectural / Design Changes

### Before
```
pr_manager.py imports:
    from mcp_coder.utils import get_default_branch_name, get_github_repository_url
```
This triggers `utils/__init__.py` execution, which imports `jenkins_operations`.

### After
```
pr_manager.py imports:
    from mcp_coder.utils.git_operations import get_default_branch_name, get_github_repository_url
```
Direct sibling import - no transitive dependencies.

### Design Principle
- **External consumers** (workflows, CLI, etc.) continue using the `utils/__init__.py` facade for convenient imports
- **Internal submodules** import directly from sibling modules to avoid loading unrelated submodules

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Modify | Change import statement |
| `.importlinter` | Modify | Remove exception and comments |

## Files Unchanged

| File | Reason |
|------|--------|
| `src/mcp_coder/utils/__init__.py` | Facade stays intact for external consumers |
| `src/mcp_coder/utils/github_operations/base_manager.py` | Already correct (imports Layer 1 `user_config`) |

## Verification

1. `lint-imports` passes without the exception
2. All existing tests pass

## Implementation Steps

- **Step 1**: Update import in `pr_manager.py` and verify with tests
- **Step 2**: Update `.importlinter` configuration and run lint-imports
