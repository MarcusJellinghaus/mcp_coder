# Step 3: Simplify create_pr/core.py Cleanup

## LLM Prompt

```
Implement Step 3 from pr_info/steps/summary.md:
Add delete_pr_info_directory() function, simplify cleanup_repository(), and remove 
the three partial delete functions from create_pr/core.py.
Follow TDD - write tests first, then implement.
```

## Overview

Replace three partial cleanup functions with a single `delete_pr_info_directory()` function.
This simplifies the cleanup logic while achieving the same result.

---

## Part A: Write Tests

### WHERE
`tests/workflows/create_pr/test_file_operations.py`

### WHAT
Add tests for `delete_pr_info_directory()`, update tests for `cleanup_repository()`.

### Test Cases

```python
class TestDeletePrInfoDirectory:
    """Tests for delete_pr_info_directory function."""

    def test_deletes_entire_pr_info_directory(self) -> None:
        """Test entire pr_info/ directory is deleted."""
        # Setup: create pr_info/ with steps/, .conversations/, TASK_TRACKER.md, Decisions.md
        # Call delete_pr_info_directory()
        # Assert: pr_info/ directory no longer exists

    def test_returns_true_when_directory_missing(self) -> None:
        """Test returns True when pr_info/ doesn't exist (no-op)."""
        # Setup: temp dir without pr_info/
        # Call delete_pr_info_directory()
        # Assert: returns True

    def test_returns_true_on_successful_deletion(self) -> None:
        """Test returns True when deletion succeeds."""
        # Setup: create pr_info/ with files
        # Call delete_pr_info_directory()
        # Assert: returns True

    def test_returns_false_on_permission_error(self) -> None:
        """Test returns False on permission error."""
        # This may be hard to test cross-platform; skip if necessary


class TestCleanupRepositorySimplified:
    """Tests for simplified cleanup_repository function."""

    def test_calls_delete_pr_info_directory(self) -> None:
        """Test cleanup_repository deletes pr_info/ directory."""
        # Setup: create pr_info/ with content
        # Call cleanup_repository()
        # Assert: pr_info/ deleted

    def test_still_cleans_profiler_output(self) -> None:
        """Test cleanup_repository still cleans profiler output."""
        # Setup: create docs/tests/performance_data/prof/ with files
        # Call cleanup_repository()
        # Assert: prof/ files deleted (directory preserved)
```

---

## Part B: Add delete_pr_info_directory Function

### WHERE
`src/mcp_coder/workflows/create_pr/core.py`

### WHAT
```python
def delete_pr_info_directory(project_dir: Path) -> bool:
    """Delete the entire pr_info/ directory and all its contents.

    Args:
        project_dir: Path to the project root directory

    Returns:
        True if successful or directory doesn't exist, False on error
    """
```

### ALGORITHM
```
1. Build path: project_dir / "pr_info"
2. If not exists: log info, return True
3. Try shutil.rmtree(pr_info_dir)
4. Log success, return True
5. On exception: log error, return False
```

### DATA
```python
# Returns: bool
# Side effects: Deletes pr_info/ directory tree
```

---

## Part C: Simplify cleanup_repository Function

### Current Implementation (to replace)
```python
def cleanup_repository(project_dir: Path) -> bool:
    success = True
    
    if not delete_steps_directory(project_dir):
        success = False
    
    if not truncate_task_tracker(project_dir):
        success = False
    
    if not clean_profiler_output(project_dir):
        success = False
    
    if not delete_conversations_directory(project_dir):
        success = False
    
    return success
```

### New Implementation
```python
def cleanup_repository(project_dir: Path) -> bool:
    """Clean up repository by deleting pr_info/ directory and profiler output.

    Args:
        project_dir: Path to project directory

    Returns:
        True if all cleanup operations succeed, False otherwise
    """
    logger.info("Cleaning up repository...")
    success = True

    # Delete entire pr_info/ directory
    logger.info("Deleting pr_info/ directory...")
    if not delete_pr_info_directory(project_dir):
        logger.error("Failed to delete pr_info directory")
        success = False

    # Clean profiler output (outside pr_info/)
    logger.info("Cleaning profiler output files...")
    if not clean_profiler_output(project_dir):
        logger.error("Failed to clean profiler output")
        success = False

    if success:
        logger.info("Repository cleanup completed successfully")
    else:
        logger.error("Repository cleanup completed with errors")

    return success
```

---

## Part D: Remove Obsolete Functions

### Functions to Delete
1. `delete_steps_directory(project_dir: Path) -> bool`
2. `delete_conversations_directory(project_dir: Path) -> bool`
3. `truncate_task_tracker(project_dir: Path) -> bool`

### Tests to Remove/Update
- Remove tests for `delete_steps_directory`
- Remove tests for `delete_conversations_directory`
- Remove tests for `truncate_task_tracker`

---

## Acceptance Criteria

- [ ] `delete_pr_info_directory()` function added
- [ ] `cleanup_repository()` simplified to use `delete_pr_info_directory()`
- [ ] `clean_profiler_output()` preserved in `cleanup_repository()`
- [ ] Three obsolete functions removed
- [ ] Related tests removed/updated
- [ ] All remaining tests pass
