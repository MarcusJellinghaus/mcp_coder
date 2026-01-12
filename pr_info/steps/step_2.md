# Step 2: Fix High-Confidence Dead Code in Source Files

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Remove the unused PullRequest import from pr_manager.py.
This is a 90% confidence finding - the import exists but is never used.
```

## WHERE
| File | Action |
|------|--------|
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Modify - remove unused import |

## WHAT

### Current code (line 12)
```python
from github.PullRequest import PullRequest
```

### Change
Remove this import line entirely - `PullRequest` type is imported but never used in the file.

## HOW
1. Open `pr_manager.py`
2. Remove line 12: `from github.PullRequest import PullRequest`
3. Verify no other code references `PullRequest`

## ALGORITHM
```
1. Read pr_manager.py
2. Locate "from github.PullRequest import PullRequest"
3. Delete the import line
4. Run pylint to verify no missing import errors
5. Run existing tests to verify no regressions
```

## VERIFICATION
```bash
# Verify removal doesn't break anything:
pylint src/mcp_coder/utils/github_operations/pr_manager.py
pytest tests/utils/github_operations/test_pr_manager.py -v
```

## DATA
No data structures changed - this is purely import cleanup.
