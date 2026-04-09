# Step 3: Move CI test classes and verify final state

## References
- Summary: `pr_info/steps/summary.md`
- Issue: #310

## WHERE

- `tests/workflows/implement/test_ci_operations.py` — **new file**
- `tests/workflows/implement/test_core.py` — remove moved test classes

## WHAT

Move CI-specific test classes from `test_core.py` to a new `test_ci_operations.py`. The class to move:

| Test Class | Tests For | Approx Lines |
|------------|-----------|--------------|
| `TestPollForCiCompletionHeartbeat` | `_poll_for_ci_completion` (heartbeat/elapsed logging) | ~180 lines (lines 2284-2463) |

## HOW

### 1. Create test_ci_operations.py

Create the new file with:

**Docstring**: `"""Tests for CI operations (ci_operations.py)."""`

**Imports** (subset needed by the moved class):
```python
import logging
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.implement.ci_operations import _poll_for_ci_completion
```

**Move** the `TestPollForCiCompletionHeartbeat` class as-is from test_core.py.

**Update `@patch` paths** within the moved class: all patches reference `mcp_coder.workflows.implement.core.time.sleep` — update to `mcp_coder.workflows.implement.ci_operations.time.sleep` since `_poll_for_ci_completion` now lives in `ci_operations`.

**Update caplog logger names**: All `caplog.at_level(logging.*, logger="mcp_coder.workflows.implement.core")` calls within `TestPollForCiCompletionHeartbeat` must change to `logger="mcp_coder.workflows.implement.ci_operations"` since the moved function's `__name__` changes.

### 2. Update test_core.py

**Remove** the `TestPollForCiCompletionHeartbeat` class (lines 2284-2463).

**Remove** the import of `_poll_for_ci_completion` that was added in Step 2 (since no tests in test_core.py use it anymore).

**Clean up unused imports** in test_core.py:
- `logging` — only used by `TestPollForCiCompletionHeartbeat`. After removal, no remaining class uses `logging`. **Remove `logging` import.**
- `Dict` from typing — `Dict` stays (used by `_make_llm_response`). Remove `logging` import (only used by heartbeat tests).

### 3. Verify exports, allowlist, and import linter

- Verify `__init__.py` exports are unchanged (`check_and_fix_ci` is not exported)
- Verify `.large-files-allowlist` — core.py stays on list (~803 lines), test_core.py stays on list (~2283 lines)
- Run `mcp-coder check file-size --max-lines 750` to confirm ci_operations.py and test_ci_operations.py are under 750
- Run import linter check

## DATA

No changes to test assertions or logic. Test classes moved as-is with import path updates only.

## ALGORITHM

```
1. Create test_ci_operations.py with imports
2. Move TestPollForCiCompletionHeartbeat class
3. Update @patch paths from core → ci_operations where functions moved
4. Update caplog logger names from core → ci_operations
5. Remove moved class from test_core.py
6. Clean up unused imports in test_core.py
7. Verify __init__.py exports, .large-files-allowlist, import linter
8. Run file-size check and all quality checks
```

## Tests

After this step, all tests should pass with `test_ci_operations.py` containing CI tests and `test_core.py` containing the remaining orchestration tests. All quality checks (pylint, pytest, mypy, import linter, vulture, file-size) must pass.

## LLM Prompt

```
Implement Step 3 from pr_info/steps/step_3.md (see also pr_info/steps/summary.md).

Move TestPollForCiCompletionHeartbeat from test_core.py to a new test_ci_operations.py. Update @patch paths and caplog logger names to point to ci_operations instead of core for moved functions. Clean up unused imports in test_core.py (remove logging, keep Dict).

Then verify: __init__.py exports unchanged, .large-files-allowlist correct, import linter passes, file-size check passes.

No logic changes — only file location and import paths change.

After changes: run pylint, pytest, mypy, import linter, vulture, file-size and fix any issues.
Write commit message to pr_info/.commit_message.txt.
```
