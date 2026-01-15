# Step 3: Final Verification and Cleanup

## LLM Prompt
```
Read pr_info/steps/summary.md for context on Issue #285.
Implement Step 3: Final verification that all tests pass and prompt_manager.py works correctly.

Requirements:
- Run all data_files tests
- Run prompt_manager tests (primary caller)
- Verify pytest-xdist parallel execution works (the original issue)
- Clean up any unused imports in data_files.py
```

## WHERE: Verification Targets

| File | Verification Type |
|------|-------------------|
| `tests/utils/test_data_files.py` | Run all tests |
| `tests/test_prompt_manager.py` | Run all tests (compatibility check) |
| `src/mcp_coder/utils/data_files.py` | Code review for unused imports |

## WHAT: Verification Commands

### 1. Run Data Files Tests
```bash
pytest tests/utils/test_data_files.py -v
```

### 2. Run Prompt Manager Tests
```bash
pytest tests/test_prompt_manager.py -v
```

### 3. Run with pytest-xdist (Original Issue)
```bash
pytest tests/utils/test_data_files.py -v -n auto
```

### 4. Run Full Test Suite
```bash
pytest tests/ -v -n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"
```

## HOW: Cleanup Checklist

### Unused Imports to Remove from data_files.py

After refactoring, these imports should no longer be needed:

```python
# REMOVE if unused:
import importlib.util  # Replaced by importlib.resources
import site            # No longer searching site-packages manually
import os              # May still need for os.name check - verify
import sys             # No longer manipulating sys.path
```

### Imports to Keep

```python
import logging
from importlib.resources import files
from pathlib import Path
from typing import List, Optional
```

## ALGORITHM: Verification Steps

```python
# 1. Run pytest tests/utils/test_data_files.py -v
#    - All tests should pass
#    - No sys.path manipulation warnings

# 2. Run pytest tests/test_prompt_manager.py -v  
#    - All tests should pass
#    - Confirms find_data_file returns compatible Path

# 3. Run pytest tests/utils/test_data_files.py -v -n auto
#    - Tests should pass in parallel
#    - This was the original pytest-xdist issue

# 4. Review data_files.py for unused imports
#    - Remove any imports no longer used
```

## DATA: Success Criteria

| Criterion | Status |
|-----------|--------|
| All `test_data_files.py` tests pass | [ ] |
| All `test_prompt_manager.py` tests pass | [ ] |
| Tests pass with `-n auto` (parallel) | [ ] |
| No unused imports in `data_files.py` | [ ] |
| Code reduced from ~500 to ~50-80 lines | [ ] |

## Post-Implementation Notes

### If Tests Fail

1. **Import errors**: Check that `importlib.resources` is imported correctly
2. **Path issues**: Verify `files().joinpath()` returns a valid Traversable
3. **Parallel test failures**: Check for any remaining mocking that might conflict

### Documentation Updates (Optional)

If time permits, update docstring in `find_data_file` to reflect:
- New implementation uses `importlib.resources`
- `development_base_dir` is deprecated
- Works automatically with editable installs
