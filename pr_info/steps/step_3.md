# Step 3: Update workspace.py - Config-Based Lookups

## LLM Prompt

```
Implement Step 3 of Issue #359 (see pr_info/steps/summary.md for context).

Task: Replace hardcoded constants in workspace.py with config-based lookups from labels.json.

Requirements:
- Remove import of HUMAN_ACTION_COMMANDS and STATUS_EMOJI from types.py
- Remove _get_stage_short() function - use vscodeclaude.stage_short from config
- Load emoji, commands, and stage_short from labels.json
- Use existing _load_labels_config() from issues.py
- Maintain identical output (same emojis, commands, stage names in generated files)
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | MODIFY - Replace constants with config lookups |
| `tests/workflows/vscodeclaude/test_workspace.py` | MODIFY - Update mocks |

## WHAT

### Remove
- Import of `HUMAN_ACTION_COMMANDS`, `STATUS_EMOJI` from `.types`
- Function `_get_stage_short()`

### Add
- Import `_load_labels_config` from `.issues`
- Helper function to get vscodeclaude config for a status

### Modify
- `create_workspace_file()` - use config for stage_short
- `create_startup_script()` - use config for emoji and commands
- `create_status_file()` - use config for emoji

### New Helper Function
```python
def _get_vscodeclaude_config(status: str) -> dict[str, Any] | None:
    """Get vscodeclaude config for a status label."""
```

## HOW

### Integration Points
- Import `_load_labels_config` from `.issues` (same module family)
- All public function signatures unchanged

### Imports
```python
# Remove:
from .types import DEFAULT_PROMPT_TIMEOUT, HUMAN_ACTION_COMMANDS, STATUS_EMOJI

# Change to:
from .types import DEFAULT_PROMPT_TIMEOUT

# Add:
from .issues import _load_labels_config
```

## ALGORITHM

```python
def _get_vscodeclaude_config(status: str) -> dict[str, Any] | None:
    """Get vscodeclaude config for a status label from labels.json."""
    labels_config = _load_labels_config()
    for label in labels_config["workflow_labels"]:
        if label["name"] == status and "vscodeclaude" in label:
            return label["vscodeclaude"]
    return None

# Usage in create_startup_script():
config = _get_vscodeclaude_config(status)
emoji = config["emoji"] if config else "📋"
initial_cmd = config["initial_command"] if config else None
```

## DATA

### Input
- `status`: String like `"status-07:code-review"`

### Output from `_get_vscodeclaude_config()`
```python
{
    "emoji": "🔍",
    "display_name": "CODE REVIEW",
    "stage_short": "review",
    "initial_command": "/implementation_review",
    "followup_command": "/discuss"
}
```

## FULL CODE CHANGE

### workspace.py - Key sections to modify

**1. Imports section:**
```python
# Before:
from .types import DEFAULT_PROMPT_TIMEOUT, HUMAN_ACTION_COMMANDS, STATUS_EMOJI

# After:
from .types import DEFAULT_PROMPT_TIMEOUT
from .issues import _load_labels_config
```

**2. Add helper function (after imports, before other functions):**
```python
def _get_vscodeclaude_config(status: str) -> dict[str, Any] | None:
    """Get vscodeclaude config for a status label.
    
    Args:
        status: Status label like "status-07:code-review"
        
    Returns:
        vscodeclaude config dict or None if not found
    """
    labels_config = _load_labels_config()
    for label in labels_config["workflow_labels"]:
        if label["name"] == status and "vscodeclaude" in label:
            return label["vscodeclaude"]
    return None
```

**3. Remove `_get_stage_short()` function entirely**

**4. Update `create_workspace_file()`:**
```python
# Before:
stage_short = _get_stage_short(status)

# After:
config = _get_vscodeclaude_config(status)
stage_short = config["stage_short"] if config else status[:6]
```

**5. Update `create_startup_script()`:**
```python
# Before:
initial_cmd, _followup_cmd = HUMAN_ACTION_COMMANDS.get(status, (None, None))
emoji = STATUS_EMOJI.get(status, "📋")

# After:
config = _get_vscodeclaude_config(status)
initial_cmd = config["initial_command"] if config else None
emoji = config["emoji"] if config else "📋"
```

**6. Update `create_status_file()`:**
```python
# Before:
status_emoji = STATUS_EMOJI.get(status, "📋")

# After:
config = _get_vscodeclaude_config(status)
status_emoji = config["emoji"] if config else "📋"
```

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_workspace.py`

**Add test for config lookup:**

```python
class TestVscodeclaudeConfigLookup:
    """Test _get_vscodeclaude_config helper function."""

    def test_returns_config_for_known_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns vscodeclaude config for known status."""
        mock_config = {
            "workflow_labels": [
                {
                    "name": "status-07:code-review",
                    "category": "human_action",
                    "vscodeclaude": {
                        "emoji": "🔍",
                        "display_name": "CODE REVIEW",
                        "stage_short": "review",
                        "initial_command": "/implementation_review",
                        "followup_command": "/discuss"
                    }
                }
            ]
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace._load_labels_config",
            lambda: mock_config
        )
        
        from mcp_coder.workflows.vscodeclaude.workspace import _get_vscodeclaude_config
        
        result = _get_vscodeclaude_config("status-07:code-review")
        assert result is not None
        assert result["emoji"] == "🔍"
        assert result["stage_short"] == "review"

    def test_returns_none_for_unknown_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns None for unknown status."""
        mock_config = {"workflow_labels": []}
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace._load_labels_config",
            lambda: mock_config
        )
        
        from mcp_coder.workflows.vscodeclaude.workspace import _get_vscodeclaude_config
        
        result = _get_vscodeclaude_config("unknown-status")
        assert result is None
```

**Update existing tests to mock `_load_labels_config` instead of constants:**

Existing tests that mock `HUMAN_ACTION_COMMANDS` or `STATUS_EMOJI` should be updated to mock `_load_labels_config` or `_get_vscodeclaude_config`.

## VERIFICATION

After implementation:
1. Run workspace tests: `pytest tests/workflows/vscodeclaude/test_workspace.py -v`
2. Verify startup scripts contain correct commands: check `/implementation_review` appears for code-review status
3. Verify workspace files contain correct stage_short values
