# Step 4: Revert Incorrect Type Ignore Comments

## Summary Reference
See [summary.md](summary.md) for overall context and design decisions.
See [Decisions.md](Decisions.md) for decisions made during plan review.

## Objective
Revert the `# type: ignore[import-untyped]` comments that were incorrectly added to `requests` imports. The `types-requests` package is already a dev dependency, so these comments are unnecessary and mask potential environment issues.

**Why this change?** During code review, it was discovered that `types-requests>=2.28.0` is already listed in `[project.optional-dependencies] dev` in `pyproject.toml`. The inline type ignore comments were added as a workaround but are incorrect—they shouldn't be needed with proper dev dependencies installed.

---

## WHERE: File Paths

| Action | File Path |
|--------|-----------|
| Modify | `src/mcp_coder/utils/github_operations/ci_results_manager.py` |
| Modify | `tests/utils/github_operations/test_ci_results_manager_artifacts.py` |
| Modify | `tests/utils/github_operations/test_ci_results_manager_foundation.py` |
| Modify | `tests/utils/github_operations/test_ci_results_manager_logs.py` |
| Modify | `tests/utils/github_operations/test_ci_results_manager_status.py` |

---

## WHAT: Changes to Make

### In each file listed above

**Current (incorrect):**
```python
import requests  # type: ignore[import-untyped]
```

**Reverted (correct):**
```python
import requests
```

---

## HOW: Integration Points

1. **No new imports or dependencies needed** - `types-requests` already in dev dependencies
2. **Simple text replacement** - Remove the inline comment from each import line
3. **Verify with mypy** - After reverting, run mypy to confirm no issues

---

## ALGORITHM: Pseudocode

```
1. For each of the 5 files:
   a. Find line containing "import requests  # type: ignore[import-untyped]"
   b. Replace with "import requests"
2. Run mypy to verify no type errors
3. If mypy fails, investigate why types-requests isn't being picked up
```

---

## DATA: No Changes to Return Values

This is a code cleanup step. No functional changes to any return values or data structures.

---

## Implementation Details

### 1. Edit `src/mcp_coder/utils/github_operations/ci_results_manager.py`

Change line 11:
```python
# Before
import requests  # type: ignore[import-untyped]

# After
import requests
```

### 2. Edit `tests/utils/github_operations/test_ci_results_manager_artifacts.py`

Change line 9:
```python
# Before
import requests  # type: ignore[import-untyped]

# After
import requests
```

### 3. Edit `tests/utils/github_operations/test_ci_results_manager_foundation.py`

Change line 9:
```python
# Before
import requests  # type: ignore[import-untyped]

# After
import requests
```

### 4. Edit `tests/utils/github_operations/test_ci_results_manager_logs.py`

Change line 9:
```python
# Before
import requests  # type: ignore[import-untyped]

# After
import requests
```

### 5. Edit `tests/utils/github_operations/test_ci_results_manager_status.py`

Change line 9:
```python
# Before
import requests  # type: ignore[import-untyped]

# After
import requests
```

---

## Verification

After reverting the comments, run:
```bash
mypy src/mcp_coder/utils/github_operations/ci_results_manager.py
mypy tests/utils/github_operations/test_ci_results_manager_artifacts.py
mypy tests/utils/github_operations/test_ci_results_manager_foundation.py
mypy tests/utils/github_operations/test_ci_results_manager_logs.py
mypy tests/utils/github_operations/test_ci_results_manager_status.py
```

**Expected Result**: No type errors. If mypy complains about missing stubs for `requests`, the issue is with the dev environment setup, not the code.

---

## LLM Prompt for Step 4

```
You are implementing Step 4 of issue #156: Support for Multi-Phase Task Tracker.

CONTEXT:
- See pr_info/steps/summary.md for overall design
- See pr_info/steps/Decisions.md for design decisions (especially Decision 16)
- See pr_info/steps/step_4.md for this step's details
- Steps 1-3 completed the main implementation
- Code review identified incorrect type ignore comments that need reverting

TASK:
1. Remove `# type: ignore[import-untyped]` from requests imports in 5 files
2. Run mypy to verify no type errors occur

REQUIREMENTS:
- Simple text replacement only
- Do not add any new type ignore comments
- types-requests is already a dev dependency, so mypy should work

FILES TO MODIFY:
- src/mcp_coder/utils/github_operations/ci_results_manager.py
- tests/utils/github_operations/test_ci_results_manager_artifacts.py
- tests/utils/github_operations/test_ci_results_manager_foundation.py
- tests/utils/github_operations/test_ci_results_manager_logs.py
- tests/utils/github_operations/test_ci_results_manager_status.py

SUCCESS CRITERIA:
- All 5 files have clean `import requests` without type ignore comments
- mypy passes on all 5 files
```
