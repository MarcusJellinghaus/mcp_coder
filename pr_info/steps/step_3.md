# Step 3: Update External Imports and Add Import Linter Contract

## LLM Prompt
```
You are implementing Step 3 of Issue #317: Refactor git_operations layered architecture.
See pr_info/steps/summary.md for full context.

This step updates external files that import from git_operations submodules
and adds the import linter contract to enforce the layered architecture.
```

## Overview
Update all external files that import directly from `git_operations` submodules to use the new `readers.py` module path, and add the import linter contract to enforce the layered architecture going forward.

---

## Part A: Update create_plan.py

### WHERE
`src/mcp_coder/workflows/create_plan.py`

### WHAT
Update import path for `is_working_directory_clean`.

### HOW
Change:
```python
from mcp_coder.utils.git_operations.repository import is_working_directory_clean
```
To:
```python
from mcp_coder.utils.git_operations.readers import is_working_directory_clean
```

### ALGORITHM
```
1. Find line: from mcp_coder.utils.git_operations.repository import is_working_directory_clean
2. Replace "repository" with "readers"
```

---

## Part B: Update ci_results_manager.py

### WHERE
`src/mcp_coder/utils/github_operations/ci_results_manager.py`

### WHAT
Update import path for `validate_branch_name`.

### HOW
Change:
```python
from mcp_coder.utils.git_operations.branches import validate_branch_name
```
To:
```python
from mcp_coder.utils.git_operations.readers import validate_branch_name
```

### ALGORITHM
```
1. Find line: from mcp_coder.utils.git_operations.branches import validate_branch_name
2. Replace "branches" with "readers"
```

---

## Part C: Update issue_manager.py

### WHERE
`src/mcp_coder/utils/github_operations/issue_manager.py`

### WHAT
Update import path for `extract_issue_number_from_branch` and `get_current_branch_name`.

### HOW
Change:
```python
from mcp_coder.utils.git_operations.branches import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
```
To:
```python
from mcp_coder.utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
```

### ALGORITHM
```
1. Find the import block from mcp_coder.utils.git_operations.branches
2. Replace "branches" with "readers"
```

---

## Part D: Update create_pr/core.py

### WHERE
`src/mcp_coder/workflows/create_pr/core.py`

### WHAT
Update import path for `extract_issue_number_from_branch`.

### HOW
Change:
```python
from mcp_coder.utils.git_operations.branches import extract_issue_number_from_branch
```
To:
```python
from mcp_coder.utils.git_operations.readers import extract_issue_number_from_branch
```

### ALGORITHM
```
1. Find line: from mcp_coder.utils.git_operations.branches import extract_issue_number_from_branch
2. Replace "branches" with "readers"
```

---

## Part E: Update set_status.py

### WHERE
`src/mcp_coder/cli/commands/set_status.py`

### WHAT
Update import path for `extract_issue_number_from_branch` and `get_current_branch_name`.

### HOW
Change:
```python
from ...utils.git_operations.branches import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
```
To:
```python
from ...utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
```

### ALGORITHM
```
1. Find the import block from ...utils.git_operations.branches
2. Replace "branches" with "readers"
```

---

## Part F: Add Import Linter Contract

### WHERE
`.importlinter`

### WHAT
Add new contract to enforce git_operations internal layering.

### HOW
Add the following contract after the existing `git_local` contract:

```ini
# -----------------------------------------------------------------------------
# Contract: Git Operations Internal Layering
# -----------------------------------------------------------------------------
# Enforces the internal layering within git_operations:
# - Command modules (branches, remotes, commits, staging, file_tracking, diffs)
#   can import from readers and core
# - Readers can only import from core
# - No imports between modules in the same layer
#
# Architecture:
#   Layer 1: branches | remotes | commits | staging | file_tracking | diffs
#   Layer 2: readers
#   Layer 3: core
# -----------------------------------------------------------------------------
[importlinter:contract:git_operations_internal_layering]
name = Git Operations Internal Layering
type = layers
layers =
    mcp_coder.utils.git_operations.branches | mcp_coder.utils.git_operations.remotes | mcp_coder.utils.git_operations.commits | mcp_coder.utils.git_operations.staging | mcp_coder.utils.git_operations.file_tracking | mcp_coder.utils.git_operations.diffs
    mcp_coder.utils.git_operations.readers
    mcp_coder.utils.git_operations.core
```

### ALGORITHM
```
1. Open .importlinter file
2. Find the [importlinter:contract:git_local] section
3. Add new contract section after it (before the THIRD-PARTY section)
4. Save file
```

### DATA - Contract explanation
The `type = layers` contract enforces:
- Modules in Layer 1 can import from Layer 2 and Layer 3
- Modules in Layer 2 can only import from Layer 3
- Modules in the same layer **cannot** import from each other
- The `|` separator means those modules are at the same layer level

---

## Verification

```bash
# Run all tests to ensure nothing broke
pytest tests/ -v --tb=short

# Run pylint on all modified files
pylint src/mcp_coder/workflows/create_plan.py
pylint src/mcp_coder/utils/github_operations/ci_results_manager.py
pylint src/mcp_coder/utils/github_operations/issue_manager.py
pylint src/mcp_coder/workflows/create_pr/core.py
pylint src/mcp_coder/cli/commands/set_status.py

# Run mypy on modified files
mypy src/mcp_coder/workflows/create_plan.py
mypy src/mcp_coder/utils/github_operations/
mypy src/mcp_coder/workflows/create_pr/core.py
mypy src/mcp_coder/cli/commands/set_status.py

# CRITICAL: Verify the import linter contract
lint-imports

# The output should show:
# - All existing contracts still pass
# - New "Git Operations Internal Layering" contract passes
```

---

## Final Verification Checklist

After completing all three steps, verify:

```bash
# 1. All tests pass
pytest tests/utils/git_operations/ -v

# 2. No pylint errors
pylint src/mcp_coder/utils/git_operations/

# 3. No mypy errors
mypy src/mcp_coder/utils/git_operations/

# 4. Import linter passes (CRITICAL)
lint-imports

# 5. Verify public API unchanged
python -c "
from mcp_coder.utils.git_operations import (
    # All these should still work
    is_git_repository,
    is_working_directory_clean,
    get_full_status,
    get_staged_changes,
    get_unstaged_changes,
    validate_branch_name,
    get_current_branch_name,
    get_default_branch_name,
    get_parent_branch_name,
    branch_exists,
    remote_branch_exists,
    extract_issue_number_from_branch,
    create_branch,
    checkout_branch,
    delete_branch,
    rebase_onto_branch,
    fetch_remote,
    git_push,
    push_branch,
    get_github_repository_url,
)
print('All exports verified!')
"
```

---

## Summary of External Import Changes

| File | Old Import | New Import |
|------|-----------|------------|
| `workflows/create_plan.py` | `...repository` | `...readers` |
| `github_operations/ci_results_manager.py` | `...branches` | `...readers` |
| `github_operations/issue_manager.py` | `...branches` | `...readers` |
| `workflows/create_pr/core.py` | `...branches` | `...readers` |
| `cli/commands/set_status.py` | `...branches` | `...readers` |

---

## Notes

- All import changes are simple path substitutions
- No function logic is changed
- The import linter contract prevents future circular dependencies
- After this step, the refactoring is complete
