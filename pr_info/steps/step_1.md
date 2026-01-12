# Step 1: Update pr_manager.py Import Statement

## LLM Prompt
```
Implement Step 1 of Issue #277. Reference: pr_info/steps/summary.md

Change the import in pr_manager.py from the utils facade to direct sibling import.
Run tests to verify no regressions.
```

## WHERE

**File to modify:**
- `src/mcp_coder/utils/github_operations/pr_manager.py`

## WHAT

Change one import statement. No new functions or signatures.

**Current import (line 13-14):**
```python
from mcp_coder.utils import get_default_branch_name, get_github_repository_url
```

**New import:**
```python
from mcp_coder.utils.git_operations import get_default_branch_name, get_github_repository_url
```

## HOW

1. Open `pr_manager.py`
2. Locate the import statement `from mcp_coder.utils import ...`
3. Replace with direct import from `mcp_coder.utils.git_operations`

## ALGORITHM

```
1. Find line: "from mcp_coder.utils import get_default_branch_name, get_github_repository_url"
2. Replace with: "from mcp_coder.utils.git_operations import get_default_branch_name, get_github_repository_url"
3. Run existing tests for pr_manager
4. Verify imports resolve correctly
```

## DATA

No data structure changes. Same functions, same signatures, different import path.

## TEST VERIFICATION

Run existing tests:
```bash
pytest tests/utils/github_operations/test_pr_manager.py -v
```

The existing tests already cover `PullRequestManager` functionality. No new tests needed since this is a pure refactoring with no behavior change.

## ACCEPTANCE CRITERIA

- [ ] Import statement changed to direct sibling import
- [ ] All `test_pr_manager.py` tests pass
- [ ] Module can be imported without errors: `python -c "from mcp_coder.utils.github_operations.pr_manager import PullRequestManager"`
