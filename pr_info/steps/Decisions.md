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

## Decision 6: Export IssueEventType

**Context:** `IssueEventType` is not currently exported from parent `__init__.py`, but the plan includes it in exports.

**Decision:** Export `IssueEventType` from `issues/__init__.py` — it's used in tests for filtering `get_issue_events()`, so it should be public.

## Decision 7: Skip LabelData in types.py

**Context:** `LabelData` already exists in `labels_manager.py` and is exported. Creating another copy in `issues/types.py` would create duplication.

**Decision:** Do NOT include `LabelData` in `issues/types.py`. Where needed, import from `labels_manager`. Consolidation can happen in #398 if desired.

## Decision 8: lint_imports Verification Timing

**Context:** Could run `lint_imports` after each step for earlier violation detection.

**Decision:** Run `lint_imports` only at Step 10d (the end). Keeps the process simpler.
