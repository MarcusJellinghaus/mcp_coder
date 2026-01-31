# Step 1: Add Template and Validation to task_tracker.py

## LLM Prompt

```
Implement Step 1 from pr_info/steps/summary.md:
Add TASK_TRACKER_TEMPLATE constant and validate_task_tracker() function to task_tracker.py.
Follow TDD - write tests first, then implement.
```

## Overview

Add the task tracker template constant and a validation function that wraps existing parsing logic.

---

## Part A: Write Tests

### WHERE
`tests/workflow_utils/test_task_tracker.py`

### WHAT
Add new test class `TestValidateTaskTracker` with tests for the validation function.

### Test Cases

```python
class TestValidateTaskTracker:
    """Tests for validate_task_tracker function."""

    def test_validate_valid_tracker(self) -> None:
        """Test validation passes for valid tracker with both headers."""
        # Create temp file with ## Tasks and ## Pull Request headers
        # Call validate_task_tracker() - should not raise

    def test_validate_missing_tasks_header(self) -> None:
        """Test validation fails when ## Tasks header missing."""
        # Create temp file without ## Tasks header
        # Call validate_task_tracker() - should raise TaskTrackerSectionNotFoundError

    def test_validate_missing_pull_request_header(self) -> None:
        """Test validation fails when ## Pull Request header missing."""
        # Create temp file with ## Tasks but no ## Pull Request
        # Call validate_task_tracker() - should raise TaskTrackerSectionNotFoundError

    def test_validate_missing_file(self) -> None:
        """Test validation fails when file doesn't exist."""
        # Call validate_task_tracker() on non-existent path
        # Should raise TaskTrackerFileNotFoundError


class TestTaskTrackerTemplate:
    """Tests for TASK_TRACKER_TEMPLATE constant."""

    def test_template_contains_tasks_header(self) -> None:
        """Test template contains ## Tasks header."""
        assert "## Tasks" in TASK_TRACKER_TEMPLATE

    def test_template_contains_pull_request_header(self) -> None:
        """Test template contains ## Pull Request header."""
        assert "## Pull Request" in TASK_TRACKER_TEMPLATE

    def test_template_is_valid(self) -> None:
        """Test template passes validation."""
        # Write template to temp file
        # Call validate_task_tracker() - should not raise
```

---

## Part B: Implement Template Constant

### WHERE
`src/mcp_coder/workflow_utils/task_tracker.py`

### WHAT
Add `TASK_TRACKER_TEMPLATE` constant after the regex patterns.

### DATA
```python
TASK_TRACKER_TEMPLATE = """# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

## Pull Request
"""
```

**Note:** This exact template was confirmed in [Decisions.md](./Decisions.md) (Decision 5).

---

## Part C: Implement Validation Function

### WHERE
`src/mcp_coder/workflow_utils/task_tracker.py`

### WHAT
```python
def validate_task_tracker(folder_path: str = "pr_info") -> None:
    """Validate TASK_TRACKER.md has required structure.
    
    Args:
        folder_path: Path to folder containing TASK_TRACKER.md
        
    Raises:
        TaskTrackerFileNotFoundError: If file doesn't exist
        TaskTrackerSectionNotFoundError: If required headers missing
    """
```

### ALGORITHM
```
1. Call _read_task_tracker(folder_path) to get content
2. Call _find_implementation_section(content) to validate headers
3. If either raises exception, let it propagate
4. Return None on success (validation passed)
```

### HOW
- Import: Add to module's public API in `__all__` if present
- Uses existing internal functions - no new dependencies

---

## Acceptance Criteria

- [ ] `TASK_TRACKER_TEMPLATE` constant defined with `## Tasks` and `## Pull Request` headers
- [ ] `validate_task_tracker()` function validates file existence and structure
- [ ] All tests pass
- [ ] No changes to existing `_find_implementation_section()` function
