# Decisions Log

Decisions made during plan review discussion.

## Decision 1: Strict Clean Break for Parent `__init__.py`

**Context:** Decision #4 in the issue states "Clean break on imports—no re-exports from parent `__init__.py`" but Step 10 showed re-exporting.

**Decision:** Strict clean break — the parent `github_operations/__init__.py` will NOT re-export any issue-related types. All consumers must import directly from the canonical path:
```python
from mcp_coder.utils.github_operations.issues import IssueManager
```

## Decision 2: Fix `_handle_github_errors` Import in Mixins

**Context:** Steps 3, 4, 5 showed `_handle_github_errors` inside `TYPE_CHECKING` block, but it's a decorator used at runtime.

**Decision:** Move `_handle_github_errors` to a regular import (outside `TYPE_CHECKING`) in all mixin files.

## Decision 3: Keep `_parse_base_branch` Internal

**Context:** The function is placed in `manager.py` but not exported via `__init__.py`.

**Decision:** Keep it internal — tests will import directly from the submodule:
```python
from mcp_coder.utils.github_operations.issues.manager import _parse_base_branch
```

## Decision 4: Split Step 10 for Incremental Verification

**Context:** Step 10 was large (14 source files, 9 test files, 3 deletions).

**Decision:** Split into 4 sub-steps that allow clean pylint/pytest/mypy runs between each:
- 10a: Update source file imports
- 10b: Update test file imports  
- 10c: Update parent `__init__.py` (remove issue exports)
- 10d: Delete old files

## Decision 5: Keep Steps 6 and 7 Separate

**Context:** Both steps move files into `issues/` directory.

**Decision:** Keep separate for easier verification of each move individually.
