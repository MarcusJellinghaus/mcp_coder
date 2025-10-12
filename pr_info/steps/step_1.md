# Step 1: Label Configuration JSON

## LLM Prompt
```
Implement Step 1 from pr_info/steps/summary.md: Create the label configuration JSON file and validation tests.

Follow Test-Driven Development:
1. Create test fixture with sample labels
2. Write tests for JSON schema validation
3. Create the actual labels.json configuration
4. Verify all tests pass
5. Run code quality checks using MCP tools

Use ONLY MCP filesystem tools for all file operations (mcp__filesystem__*).
```

## WHERE: File Paths

### Files to CREATE
```
workflows/config/labels.json                    # Main label configuration
tests/workflows/config/test_labels.json         # Test fixture
tests/workflows/test_issue_stats.py            # Test file (skeleton for now)
```

### Directory Structure
```
workflows/
  config/
    labels.json
tests/
  workflows/
    config/
      test_labels.json
    test_issue_stats.py
```

## WHAT: Main Components

### 1. Label Configuration Schema (labels.json)
```json
{
  "workflow_labels": [
    {
      "internal_id": "created",
      "name": "status-01:created",
      "color": "10b981",
      "description": "Fresh issue, may need refinement",
      "category": "human_action"
    }
  ]
}
```

**Fields:**
- `internal_id` (string): Short identifier for code references
- `name` (string): Full GitHub label name (status-NN:name format)
- `color` (string): 6-character hex code (no # prefix)
- `description` (string): Human-readable label purpose
- `category` (string): One of: human_action, bot_pickup, bot_busy

### 2. Test Fixture (test_labels.json)
Minimal subset for testing:
- 2 human_action labels
- 1 bot_pickup label
- 1 bot_busy label

### 3. Test Functions (test_issue_stats.py - skeleton)
```python
def test_load_labels_json():
    """Test loading and parsing labels.json"""
    pass

def test_labels_json_schema_valid():
    """Test all required fields present and valid"""
    pass

def test_category_values_valid():
    """Test category is one of: human_action, bot_pickup, bot_busy"""
    pass
```

## HOW: Integration Points

### JSON Loading Pattern
```python
import json
from pathlib import Path

def load_labels_config(config_path: Path) -> dict:
    """Load label configuration from JSON file.
    
    Args:
        config_path: Path to labels.json
        
    Returns:
        Dict with 'workflow_labels' key containing list of label configs
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

### Validation Pattern
```python
def validate_label_config(config: dict) -> bool:
    """Validate label configuration structure.
    
    Returns:
        True if valid, raises ValueError otherwise
    """
    # Check workflow_labels key exists
    # Check each label has required fields
    # Check category is valid
    # Check color format (6-char hex)
    # Check name matches status-NN:* pattern
```

## ALGORITHM: JSON Schema Validation

```
FUNCTION validate_label_config(config):
    IF 'workflow_labels' NOT IN config:
        RAISE ValueError("Missing workflow_labels key")
    
    FOR EACH label IN config['workflow_labels']:
        VALIDATE required_fields = {internal_id, name, color, description, category}
        VALIDATE category IN {human_action, bot_pickup, bot_busy}
        VALIDATE color matches regex ^[0-9A-Fa-f]{6}$
        VALIDATE name matches regex ^status-\d{2}:.+$
    
    RETURN True
```

## DATA: Label Configuration Content

### Complete labels.json (10 workflow statuses)
```json
{
  "workflow_labels": [
    {
      "internal_id": "created",
      "name": "status-01:created",
      "color": "10b981",
      "description": "Fresh issue, may need refinement",
      "category": "human_action"
    },
    {
      "internal_id": "awaiting_planning",
      "name": "status-02:awaiting-planning",
      "color": "6ee7b7",
      "description": "Issue is refined and ready for implementation planning",
      "category": "bot_pickup"
    },
    {
      "internal_id": "planning",
      "name": "status-03:planning",
      "color": "a7f3d0",
      "description": "Implementation plan being drafted (auto/in-progress)",
      "category": "bot_busy"
    },
    {
      "internal_id": "plan_review",
      "name": "status-04:plan-review",
      "color": "3b82f6",
      "description": "First implementation plan available for review/discussion",
      "category": "human_action"
    },
    {
      "internal_id": "plan_ready",
      "name": "status-05:plan-ready",
      "color": "93c5fd",
      "description": "Implementation plan approved, ready to code",
      "category": "bot_pickup"
    },
    {
      "internal_id": "implementing",
      "name": "status-06:implementing",
      "color": "bfdbfe",
      "description": "Code being written (auto/in-progress)",
      "category": "bot_busy"
    },
    {
      "internal_id": "code_review",
      "name": "status-07:code-review",
      "color": "f59e0b",
      "description": "Implementation complete, needs code review",
      "category": "human_action"
    },
    {
      "internal_id": "ready_pr",
      "name": "status-08:ready-pr",
      "color": "fbbf24",
      "description": "Approved for pull request creation",
      "category": "bot_pickup"
    },
    {
      "internal_id": "pr_creating",
      "name": "status-09:pr-creating",
      "color": "fed7aa",
      "description": "Bot is creating the pull request (auto/in-progress)",
      "category": "bot_busy"
    },
    {
      "internal_id": "pr_created",
      "name": "status-10:pr-created",
      "color": "8b5cf6",
      "description": "Pull request created, awaiting approval/merge",
      "category": "human_action"
    }
  ]
}
```

### Test Fixture (test_labels.json - minimal)
```json
{
  "workflow_labels": [
    {
      "internal_id": "created",
      "name": "status-01:created",
      "color": "10b981",
      "description": "Fresh issue",
      "category": "human_action"
    },
    {
      "internal_id": "plan_review",
      "name": "status-04:plan-review",
      "color": "3b82f6",
      "description": "Plan review",
      "category": "human_action"
    },
    {
      "internal_id": "awaiting_planning",
      "name": "status-02:awaiting-planning",
      "color": "6ee7b7",
      "description": "Ready for planning",
      "category": "bot_pickup"
    },
    {
      "internal_id": "implementing",
      "name": "status-06:implementing",
      "color": "bfdbfe",
      "description": "Coding in progress",
      "category": "bot_busy"
    }
  ]
}
```

## Implementation Checklist
- [ ] Create workflows/config/ directory
- [ ] Create tests/workflows/config/ directory
- [ ] Write labels.json with all 10 workflow statuses
- [ ] Write test_labels.json fixture with 4 minimal statuses
- [ ] Create test_issue_stats.py skeleton with 3 test functions
- [ ] Run tests: `mcp__code-checker__run_pytest_check` with fast unit test exclusions
- [ ] Verify JSON files are valid and parseable
- [ ] All tests pass

## Quality Checks
```python
# After implementation, run:
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)
```

## Expected Test Output
```
tests/workflows/test_issue_stats.py::test_load_labels_json PASSED
tests/workflows/test_issue_stats.py::test_labels_json_schema_valid PASSED
tests/workflows/test_issue_stats.py::test_category_values_valid PASSED
```
