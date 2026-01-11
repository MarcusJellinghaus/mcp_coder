# Issue #269: Move commit_operations to application layer

## Summary

This refactoring moves `commit_operations.py` from the infrastructure layer (`utils/`) to the application layer (`workflow_utils/`) to fix an architectural dependency violation.

## Problem

`src/mcp_coder/utils/commit_operations.py` imports from domain layer modules:
- `llm.env`, `llm.interface`, `llm.providers.claude`
- `prompt_manager`

This violates the layered architecture principle: **infrastructure should not depend on domain/application layers**.

## Solution

Move `commit_operations.py` to `workflow_utils/` because it:
- Orchestrates multiple services (git + LLM + prompts)
- Implements a use case (generate commit message)
- Belongs with other workflow utilities like `task_tracker.py`

---

## Architectural Changes

### Before
```
src/mcp_coder/
├── utils/                    # Infrastructure layer
│   └── commit_operations.py  # VIOLATION: imports from llm/, prompt_manager
├── llm/                      # Domain layer
└── workflow_utils/           # Application layer
```

### After
```
src/mcp_coder/
├── utils/                    # Infrastructure layer (no domain imports)
├── llm/                      # Domain layer
└── workflow_utils/           # Application layer
    ├── task_tracker.py
    └── commit_operations.py  # MOVED: properly in application layer
```

---

## Files to Modify

| File | Action |
|------|--------|
| `src/mcp_coder/utils/commit_operations.py` | **DELETE** |
| `src/mcp_coder/workflow_utils/commit_operations.py` | **CREATE** (moved content) |
| `src/mcp_coder/cli/commands/commit.py` | Update import path |
| `src/mcp_coder/workflows/implement/task_processing.py` | Update import path |
| `tests/utils/test_commit_operations.py` | **DELETE** |
| `tests/workflow_utils/test_commit_operations.py` | **CREATE** (moved content) |
| `tests/cli/commands/test_commit.py` | Update import and mock paths |

---

## Implementation Steps Overview

| Step | Description |
|------|-------------|
| 1 | Move source file and update its internal import |
| 2 | Move test file and update all import/mock paths |
| 3 | Update imports in dependent source files |
| 4 | Verify all tests pass |

---

## Key Technical Details

### Import Change in Moved File
The only internal import that changes:
```python
# Before (in utils/)
from .git_operations import get_git_diff_for_commit, stage_all_changes

# After (in workflow_utils/)
from ..utils.git_operations import get_git_diff_for_commit, stage_all_changes
```

### Import Changes in Dependent Files
```python
# Before
from mcp_coder.utils.commit_operations import generate_commit_message_with_llm

# After
from mcp_coder.workflow_utils.commit_operations import generate_commit_message_with_llm
```

---

## Design Decisions

1. **No `__init__.py` exports**: Direct module imports are used throughout the codebase. Adding package-level exports would add complexity without benefit (YAGNI).

2. **Test file follows source**: Test moves from `tests/utils/` to `tests/workflow_utils/` to mirror source structure.

3. **Minimal changes**: Only import paths change; no functional modifications to the code.
