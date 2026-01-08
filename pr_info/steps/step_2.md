# Step 2: Implement Conversations Directory Deletion

## LLM Prompt

```
Implement Step 2 from pr_info/steps/step_2.md for Issue #259.
Reference: pr_info/steps/summary.md

This step implements the actual deletion of `pr_info/.conversations/` 
directory in the `cleanup_repository()` function and updates the commit message.
After this step, the test from Step 1 should pass.
```

## WHERE: File Paths

- **Source file**: `src/mcp_coder/workflows/create_pr/core.py`

## WHAT: Modifications

### 1. Update `cleanup_repository()` function

Add deletion logic for `.conversations` directory after the existing cleanup operations.

### 2. Update commit message in `run_create_pr_workflow()`

Change the commit message to reflect that conversations folder is also cleaned.

## HOW: Integration Points

- Add code inside `cleanup_repository()` function (around line 310-315)
- Update commit message string in `run_create_pr_workflow()` (around line 380)
- Uses existing `shutil` import (already present)
- Uses existing `logger` (already present)

## ALGORITHM: Deletion Pseudocode

```python
# In cleanup_repository(), after clean_profiler_output():

1. conversations_dir = project_dir / "pr_info" / ".conversations"
2. if conversations_dir.exists():
3.     try:
4.         shutil.rmtree(conversations_dir)
5.         logger.info(f"Successfully deleted: {conversations_dir}")
6.     except Exception as e:
7.         logger.error(f"Failed to delete conversations: {e}")
8.         success = False
9. else:
10.    logger.info(f"Directory {conversations_dir} does not exist - nothing to delete")
```

## DATA: Function Behavior

- **Input**: `project_dir: Path`
- **Output**: `bool` (unchanged - True if all operations succeed)
- **Side effect**: Deletes `pr_info/.conversations/` if it exists

## Code Changes Summary

### Change 1: Update docstring of `cleanup_repository()`

```python
def cleanup_repository(project_dir: Path) -> bool:
    """
    Clean up repository by deleting steps directory, conversations directory,
    truncating task tracker, and cleaning profiler output.
    ...
    """
```

### Change 2: Add conversations deletion in `cleanup_repository()`

Add after the `clean_profiler_output()` call block.

### Change 3: Update commit message

```python
# Old:
commit_result = commit_all_changes(
    "Clean up pr_info/steps planning files", project_dir
)

# New:
commit_result = commit_all_changes(
    "Clean up pr_info temporary folders", project_dir
)
```

## Verification

After implementing:
1. Run test from Step 1: `pytest tests/workflows/create_pr/test_repository.py -v -k conversations`
2. Run all create_pr tests: `pytest tests/workflows/create_pr/ -v`
3. Run full test suite to ensure no regressions
