# Step 3: Move CI test classes to test_ci_operations.py

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

### 2. Update test_core.py

**Remove** the `TestPollForCiCompletionHeartbeat` class (lines 2284-2463).

**Remove** the import of `_poll_for_ci_completion` that was added in Step 2 (since no tests in test_core.py use it anymore).

**Clean up unused imports** in test_core.py:
- `logging` — check if still used by remaining test classes. It's used in `TestPollForCiCompletionHeartbeat` only. After removal, check if any other class uses `logging`... Looking at the imports used: `caplog: pytest.LogCaptureFixture` doesn't require importing `logging`, but `caplog.at_level(logging.INFO, ...)` does. After removing the heartbeat test class, check remaining usages. If no remaining class uses `logging`, remove it. Otherwise keep it.
- `Dict` from typing — check if still used after removal. The heartbeat tests use `Dict[str, Any]`. If no remaining test uses `Dict`, remove it.

### 3. No changes to other test files

`tests/workflows/implement/test_ci_check.py` tests functions from `mcp_coder.checks.branch_status`, not from `ci_operations`. It stays unchanged.

## DATA

No changes to test assertions or logic. Test classes moved as-is with import path updates only.

## ALGORITHM

```
1. Create test_ci_operations.py with imports
2. Move TestPollForCiCompletionHeartbeat class
3. Update @patch paths from core → ci_operations where functions moved
4. Remove moved class from test_core.py
5. Clean up unused imports in test_core.py
```

## Tests

After this step, all tests should pass with `test_ci_operations.py` containing CI tests and `test_core.py` containing the remaining orchestration tests.

## LLM Prompt

```
Implement Step 3 from pr_info/steps/step_3.md (see also pr_info/steps/summary.md).

Move TestPollForCiCompletionHeartbeat from test_core.py to a new test_ci_operations.py. Update @patch paths to point to ci_operations instead of core for moved functions. Clean up unused imports in test_core.py.

No logic changes — only file location and import paths change.

After changes: run pylint, pytest, mypy and fix any issues.
Write commit message to pr_info/.commit_message.txt.
```
