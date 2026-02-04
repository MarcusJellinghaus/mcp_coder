# Step 1: Config Update and Ignore-Label Helper Functions

## LLM Prompt

```
Implement Step 1 of Issue #400 (see pr_info/steps/summary.md for context).

This step adds blocked/wait labels to config and creates helper functions for ignore-label detection.

Follow TDD: Write tests first, then implement the functionality.
```

## Overview

Add `blocked` and `wait` to `ignore_labels` config and create two helper functions in `issues.py` for reusable ignore-label logic.

---

## Part A: Update labels.json

### WHERE
- `src/mcp_coder/config/labels.json`

### WHAT
Add `blocked` and `wait` to the `ignore_labels` array.

### CHANGE
```json
// Before
"ignore_labels": ["Overview"]

// After  
"ignore_labels": ["Overview", "blocked", "wait"]
```

---

## Part B: Add Helper Functions to issues.py

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/issues.py`
- `tests/workflows/vscodeclaude/test_issues.py`

### WHAT

#### Function 1: `get_ignore_labels`
```python
def get_ignore_labels() -> set[str]:
    """Get set of ignore labels from labels.json (lowercase for case-insensitive matching).
    
    Returns:
        Set of lowercase label names to ignore
    """
```

#### Function 2: `get_matching_ignore_label`
```python
def get_matching_ignore_label(
    issue_labels: list[str],
    ignore_labels: set[str],
) -> str | None:
    """Find first matching ignore label in issue's labels (case-insensitive).
    
    Args:
        issue_labels: List of label names from the issue
        ignore_labels: Set of lowercase ignore label names
        
    Returns:
        The original label name if match found, None otherwise
    """
```

### HOW
- Add to existing imports section (none needed - uses existing `_load_labels_config`)
- Functions go after existing helper functions
- Note: No `__all__` needed - keep consistent with current module style

### ALGORITHM

**get_ignore_labels:**
```
1. Call _load_labels_config() to get config dict
2. Get "ignore_labels" list from config (default empty)
3. Return set of lowercase labels
```

**get_matching_ignore_label:**
```
1. For each label in issue_labels:
2.   If label.lower() in ignore_labels:
3.     Return original label (preserves case)
4. Return None
```

### DATA

**get_ignore_labels returns:**
```python
{"overview", "blocked", "wait"}  # lowercase set
```

**get_matching_ignore_label returns:**
```python
# Input: issue_labels=["status-01:created", "Blocked"], ignore_labels={"blocked", "wait"}
# Output: "Blocked"  # Original case preserved

# Input: issue_labels=["status-01:created"], ignore_labels={"blocked", "wait"}  
# Output: None
```

---

## Part C: Tests

### WHERE
- `tests/workflows/vscodeclaude/test_issues.py`

### TEST CASES

```python
class TestGetIgnoreLabels:
    """Tests for get_ignore_labels function."""
    
    def test_returns_set_of_lowercase_labels(self):
        """Should return ignore_labels as lowercase set."""
        result = get_ignore_labels()
        assert isinstance(result, set)
        assert "blocked" in result
        assert "wait" in result
        assert "overview" in result
        
    def test_all_labels_are_lowercase(self):
        """All returned labels should be lowercase."""
        result = get_ignore_labels()
        for label in result:
            assert label == label.lower()


class TestGetMatchingIgnoreLabel:
    """Tests for get_matching_ignore_label function."""
    
    def test_finds_exact_match(self):
        """Should find label with exact case."""
        result = get_matching_ignore_label(
            ["status-01:created", "blocked"],
            {"blocked", "wait"}
        )
        assert result == "blocked"
        
    def test_finds_case_insensitive_match(self):
        """Should match regardless of case."""
        result = get_matching_ignore_label(
            ["status-01:created", "Blocked"],
            {"blocked", "wait"}
        )
        assert result == "Blocked"  # Preserves original case
        
    def test_finds_uppercase_match(self):
        """Should match UPPERCASE labels."""
        result = get_matching_ignore_label(
            ["WAIT", "status-04:plan-review"],
            {"blocked", "wait"}
        )
        assert result == "WAIT"
        
    def test_returns_first_match(self):
        """Should return first matching label."""
        result = get_matching_ignore_label(
            ["blocked", "wait"],
            {"blocked", "wait"}
        )
        assert result == "blocked"  # First one
        
    def test_returns_none_when_no_match(self):
        """Should return None when no ignore labels found."""
        result = get_matching_ignore_label(
            ["status-01:created", "bug"],
            {"blocked", "wait"}
        )
        assert result is None
        
    def test_handles_empty_issue_labels(self):
        """Should handle empty issue labels list."""
        result = get_matching_ignore_label([], {"blocked", "wait"})
        assert result is None
        
    def test_handles_empty_ignore_labels(self):
        """Should handle empty ignore labels set."""
        result = get_matching_ignore_label(["blocked"], set())
        assert result is None
```

---

## Verification

After implementation, run:
```bash
pytest tests/workflows/vscodeclaude/test_issues.py -v -k "ignore"
```

All tests should pass, confirming:
1. `get_ignore_labels()` returns lowercase set including `blocked` and `wait`
2. `get_matching_ignore_label()` performs case-insensitive matching
3. Original label case is preserved in return value
