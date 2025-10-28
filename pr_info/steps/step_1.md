# Step 1: Label Configuration Loading (TDD)

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.

## Objective
Implement label configuration loading from `workflows/config/labels.json` to support workflow automation.

## WHERE

**Test File:**
- `tests/cli/commands/test_coordinator.py`
- Add new test class: `TestLoadLabelConfig`

**Implementation File:**
- `src/mcp_coder/cli/commands/coordinator.py`
- Add function after existing helper functions (after `format_job_output`)

## WHAT

### Test Class (TDD First)

```python
class TestLoadLabelConfig:
    """Tests for load_label_config function."""
    
    def test_load_label_config_success() -> None:
        """Test loading valid label configuration."""
        # Verify returns dict with bot_pickup, bot_busy, ignore_labels
        
    def test_load_label_config_file_not_found() -> None:
        """Test error handling when labels.json missing."""
        # Verify raises FileNotFoundError with helpful message
        
    def test_load_label_config_invalid_json() -> None:
        """Test error handling for malformed JSON."""
        # Verify raises ValueError with parsing error
```

### Main Function Signature

```python
def load_label_config() -> dict[str, list[str]]:
    """Load workflow label configuration from labels.json.
    
    Returns:
        Dict with keys:
        - "bot_pickup": List of labels that trigger automation (status-02, 05, 08)
        - "bot_busy": List of labels for in-progress workflows (status-03, 06, 09)
        - "ignore_labels": List of labels to skip (e.g., "Overview")
        
    Raises:
        FileNotFoundError: If labels.json not found
        ValueError: If JSON is invalid or missing required fields
    """
```

## HOW

### Integration Points

**Imports:**
```python
import json
from pathlib import Path
from typing import Any
```

**File Location:**
```python
# Relative to project root
LABELS_FILE = Path(__file__).parent.parent.parent.parent / "workflows" / "config" / "labels.json"
```

**Usage in coordinator run:**
```python
def execute_coordinator_run(args: Namespace) -> int:
    # Load label configuration
    label_config = load_label_config()
    bot_pickup_labels = label_config["bot_pickup"]
    ignore_labels = label_config["ignore_labels"]
    # ... use in filtering
```

## ALGORITHM

```
1. Construct path to workflows/config/labels.json
2. Check if file exists → raise FileNotFoundError if missing
3. Read and parse JSON → raise ValueError if invalid
4. Extract workflow_labels array
5. Filter by category: bot_pickup, bot_busy
6. Extract ignore_labels array
7. Return dict with three lists
```

## DATA

### Input File Structure (labels.json)
```json
{
  "workflow_labels": [
    {"internal_id": "awaiting_planning", "name": "status-02:awaiting-planning", "category": "bot_pickup"},
    {"internal_id": "planning", "name": "status-03:planning", "category": "bot_busy"},
    {"internal_id": "plan_ready", "name": "status-05:plan-ready", "category": "bot_pickup"},
    {"internal_id": "implementing", "name": "status-06:implementing", "category": "bot_busy"},
    {"internal_id": "ready_pr", "name": "status-08:ready-pr", "category": "bot_pickup"},
    {"internal_id": "pr_creating", "name": "status-09:pr-creating", "category": "bot_busy"}
  ],
  "ignore_labels": ["Overview"]
}
```

### Return Value
```python
{
    "bot_pickup": [
        "status-02:awaiting-planning",
        "status-05:plan-ready", 
        "status-08:ready-pr"
    ],
    "bot_busy": [
        "status-03:planning",
        "status-06:implementing",
        "status-09:pr-creating"
    ],
    "ignore_labels": ["Overview"]
}
```

## Implementation Notes

1. **Error Handling:** Use clear error messages for missing file or invalid JSON
2. **Path Resolution:** Use `Path(__file__)` for robust path construction
3. **Validation:** Verify workflow_labels and ignore_labels keys exist
4. **Simplicity:** No caching, no complex parsing - just read and filter

## LLM Prompt for Implementation

```
Implement Step 1 of the coordinator run feature as described in pr_info/steps/summary.md.

Task: Add label configuration loading to src/mcp_coder/cli/commands/coordinator.py

Requirements:
1. First write tests in tests/cli/commands/test_coordinator.py:
   - TestLoadLabelConfig class with 3 test methods
   - Test success case, file not found, invalid JSON
   
2. Then implement load_label_config() function:
   - Read workflows/config/labels.json
   - Parse and filter by category (bot_pickup, bot_busy)
   - Return dict with three lists
   - Handle errors with clear messages

3. Run code quality checks:
   - mcp__code-checker__run_pytest_check with fast unit tests
   - mcp__code-checker__run_pylint_check
   - mcp__code-checker__run_mypy_check

Follow the exact signatures and data structures in step_1.md.
Use KISS principle - simple, readable code.
```

## Test Execution

**Run fast unit tests only:**
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"],
    show_details=False
)
```

## Success Criteria

- ✅ All 3 tests pass
- ✅ Function loads labels.json correctly
- ✅ Returns proper dict structure
- ✅ Error handling works (FileNotFoundError, ValueError)
- ✅ Pylint/mypy checks pass
- ✅ Code follows existing coordinator.py style
