# Step 4: Update helpers.py - Config-Based Display Names

## LLM Prompt

```
Implement Step 4 of Issue #359 (see pr_info/steps/summary.md for context).

Task: Replace STAGE_DISPLAY_NAMES constant in helpers.py with config-based lookup from labels.json.

Requirements:
- Remove import of STAGE_DISPLAY_NAMES from types.py
- Load display names from vscodeclaude.display_name in labels.json
- Use _load_labels_config() from issues.py
- Maintain identical output (same display names)
- Fallback to status.upper() for unknown statuses (unchanged behavior)
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/helpers.py` | MODIFY - Replace constant with config lookup |
| `tests/workflows/vscodeclaude/test_helpers.py` | MODIFY - Update tests |

## WHAT

### Remove
- Import of `STAGE_DISPLAY_NAMES` from `.types`

### Add
- Import `_load_labels_config` from `.issues`

### Modify
- `get_stage_display_name()` - use config lookup instead of constant

### Function Signature (unchanged)
```python
def get_stage_display_name(status: str) -> str:
    """Get human-readable stage name for display."""
```

## HOW

### Integration Points
- Import `_load_labels_config` from `.issues`
- Function signature unchanged - no impact on callers

### Imports
```python
# Remove:
from .types import (
    STAGE_DISPLAY_NAMES,
    VSCodeClaudeSession,
)

# Change to:
from .types import VSCodeClaudeSession

# Add:
from .issues import _load_labels_config
```

## ALGORITHM

```python
def get_stage_display_name(status: str) -> str:
    """Get human-readable stage name for display."""
    labels_config = _load_labels_config()
    for label in labels_config["workflow_labels"]:
        if label["name"] == status and "vscodeclaude" in label:
            return label["vscodeclaude"]["display_name"]
    return status.upper()  # Fallback unchanged
```

## DATA

### Input
- `status`: String like `"status-07:code-review"`

### Output
- String like `"CODE REVIEW"`

### Mapping (from labels.json after Step 1)
| Status | Display Name |
|--------|--------------|
| `status-01:created` | ISSUE ANALYSIS |
| `status-04:plan-review` | PLAN REVIEW |
| `status-07:code-review` | CODE REVIEW |
| `status-10:pr-created` | PR CREATED |

## FULL CODE CHANGE

### helpers.py

**Before:**
```python
from .types import (
    STAGE_DISPLAY_NAMES,
    VSCodeClaudeSession,
)


def get_stage_display_name(status: str) -> str:
    """Get human-readable stage name for display.

    Args:
        status: Status label (e.g., "status-07:code-review")

    Returns:
        Display name (e.g., "CODE REVIEW")
    """
    return STAGE_DISPLAY_NAMES.get(status, status.upper())
```

**After:**
```python
from .types import VSCodeClaudeSession
from .issues import _load_labels_config


def get_stage_display_name(status: str) -> str:
    """Get human-readable stage name for display.

    Args:
        status: Status label (e.g., "status-07:code-review")

    Returns:
        Display name (e.g., "CODE REVIEW")
    """
    labels_config = _load_labels_config()
    for label in labels_config["workflow_labels"]:
        if label["name"] == status and "vscodeclaude" in label:
            return label["vscodeclaude"]["display_name"]
    return status.upper()
```

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_helpers.py`

**Update existing tests to use mocks:**

```python
class TestDisplayHelpers:
    """Test display helper functions."""

    def test_get_stage_display_name_known_statuses(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns human-readable stage names."""
        mock_config = {
            "workflow_labels": [
                {
                    "name": "status-07:code-review",
                    "category": "human_action",
                    "vscodeclaude": {"display_name": "CODE REVIEW", "emoji": "🔍", "stage_short": "review", "initial_command": "/implementation_review", "followup_command": "/discuss"}
                },
                {
                    "name": "status-04:plan-review",
                    "category": "human_action",
                    "vscodeclaude": {"display_name": "PLAN REVIEW", "emoji": "📋", "stage_short": "plan", "initial_command": "/plan_review", "followup_command": "/discuss"}
                },
                {
                    "name": "status-01:created",
                    "category": "human_action",
                    "vscodeclaude": {"display_name": "ISSUE ANALYSIS", "emoji": "📝", "stage_short": "new", "initial_command": "/issue_analyse", "followup_command": "/discuss"}
                },
                {
                    "name": "status-10:pr-created",
                    "category": "human_action",
                    "vscodeclaude": {"display_name": "PR CREATED", "emoji": "🎉", "stage_short": "pr", "initial_command": None, "followup_command": None}
                },
            ]
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.helpers._load_labels_config",
            lambda: mock_config
        )
        
        from mcp_coder.workflows.vscodeclaude.helpers import get_stage_display_name
        
        assert get_stage_display_name("status-07:code-review") == "CODE REVIEW"
        assert get_stage_display_name("status-04:plan-review") == "PLAN REVIEW"
        assert get_stage_display_name("status-01:created") == "ISSUE ANALYSIS"
        assert get_stage_display_name("status-10:pr-created") == "PR CREATED"

    def test_get_stage_display_name_unknown_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns uppercased status for unknown statuses."""
        mock_config = {"workflow_labels": []}
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.helpers._load_labels_config",
            lambda: mock_config
        )
        
        from mcp_coder.workflows.vscodeclaude.helpers import get_stage_display_name
        
        result = get_stage_display_name("unknown-status")
        assert result == "UNKNOWN-STATUS"
```

**Remove test that asserts STAGE_DISPLAY_NAMES coverage:**

```python
# REMOVE this test - constant no longer exists
def test_stage_display_names_coverage(self) -> None:
    """All priority statuses have display names."""
    for status in VSCODECLAUDE_PRIORITY:
        assert status in STAGE_DISPLAY_NAMES
```

## VERIFICATION

After implementation:
1. Run helpers tests: `pytest tests/workflows/vscodeclaude/test_helpers.py -v`
2. Verify display names match expected values
3. Verify fallback works for unknown statuses
