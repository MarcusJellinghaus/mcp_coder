# Step 1: Rename _update_issue_labels_in_cache to public function

## LLM Prompt
```
You are implementing Issue #365: Refactor coordinator - Remove _get_coordinator() late-binding pattern.
See pr_info/steps/summary.md for full context.

This is Step 1: Rename the private function `_update_issue_labels_in_cache` to `update_issue_labels_in_cache` 
in the issue_cache module, making it public since it's used across modules.
```

## WHERE

### File to Modify
- `src/mcp_coder/utils/github_operations/issue_cache.py`

## WHAT

### Function Rename
```python
# Before
def _update_issue_labels_in_cache(
    repo_full_name: str, issue_number: int, old_label: str, new_label: str
) -> None:

# After  
def update_issue_labels_in_cache(
    repo_full_name: str, issue_number: int, old_label: str, new_label: str
) -> None:
```

## HOW

1. Find the function definition `def _update_issue_labels_in_cache(`
2. Rename to `def update_issue_labels_in_cache(`
3. Update the docstring if it references the private name (it doesn't)
4. No logic changes required

## ALGORITHM
```
1. Open issue_cache.py
2. Find function definition starting with "def _update_issue_labels_in_cache"
3. Remove leading underscore from function name
4. Save file
```

## DATA

### Function Signature (unchanged except name)
```python
def update_issue_labels_in_cache(
    repo_full_name: str,    # e.g., "owner/repo"
    issue_number: int,      # GitHub issue number
    old_label: str,         # Label to remove
    new_label: str,         # Label to add
) -> None:
```

## TEST CONSIDERATIONS

This is a simple rename - no new tests needed. Existing tests in `tests/utils/github_operations/test_issue_cache.py` will be updated in Step 5 when we update test patch locations.

## VERIFICATION

After this step:
```bash
# Should find 0 occurrences of the old name in issue_cache.py
grep "_update_issue_labels_in_cache" src/mcp_coder/utils/github_operations/issue_cache.py

# Should find the new function
grep "def update_issue_labels_in_cache" src/mcp_coder/utils/github_operations/issue_cache.py
```
