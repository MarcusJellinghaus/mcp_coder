# Step 1: Extend labels.json with vscodeclaude Metadata

## LLM Prompt

```
Implement Step 1 of Issue #359 (see pr_info/steps/summary.md for context).

Task: Add vscodeclaude metadata to the 4 human_action labels in labels.json.

Requirements:
- Add a "vscodeclaude" object to each human_action label
- All fields required: emoji, display_name, stage_short, initial_command, followup_command
- For status-10:pr-created, commands are null (show PR URL only)
- Preserve existing label structure and all other labels unchanged
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/config/labels.json` | MODIFY - Add vscodeclaude objects |
| `tests/workflows/vscodeclaude/test_types.py` | MODIFY - Add schema validation test |

## WHAT

### labels.json Changes

Add `vscodeclaude` object to each of the 4 human_action labels:

| Label | emoji | display_name | stage_short | initial_command | followup_command |
|-------|-------|--------------|-------------|-----------------|------------------|
| `status-01:created` | 📝 | ISSUE ANALYSIS | new | /issue_analyse | /discuss |
| `status-04:plan-review` | 📋 | PLAN REVIEW | plan | /plan_review | /discuss |
| `status-07:code-review` | 🔍 | CODE REVIEW | review | /implementation_review | /discuss |
| `status-10:pr-created` | 🎉 | PR CREATED | pr | null | null |

### Test Function

```python
def test_human_action_labels_have_vscodeclaude_metadata() -> None:
    """All human_action labels have required vscodeclaude fields."""
```

## HOW

### Integration Points
- No code changes needed - just JSON data
- Existing `_load_labels_config()` in `issues.py` will automatically load new fields

### Imports
- None (JSON file modification)

## ALGORITHM

```
For each label in workflow_labels where category == "human_action":
    Add vscodeclaude object with:
        emoji = STATUS_EMOJI[label_name]
        display_name = STAGE_DISPLAY_NAMES[label_name]
        stage_short = _get_stage_short() mapping
        initial_command = HUMAN_ACTION_COMMANDS[label_name][0]
        followup_command = HUMAN_ACTION_COMMANDS[label_name][1]
```

## DATA

### Input: Current labels.json human_action entry
```json
{
  "internal_id": "created",
  "name": "status-01:created",
  "color": "10b981",
  "description": "Fresh issue, may need refinement",
  "category": "human_action"
}
```

### Output: Extended labels.json human_action entry
```json
{
  "internal_id": "created",
  "name": "status-01:created",
  "color": "10b981",
  "description": "Fresh issue, may need refinement",
  "category": "human_action",
  "vscodeclaude": {
    "emoji": "📝",
    "display_name": "ISSUE ANALYSIS",
    "stage_short": "new",
    "initial_command": "/issue_analyse",
    "followup_command": "/discuss"
  }
}
```

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_types.py`

Add new test class:

```python
class TestLabelsJsonVscodeclaudeMetadata:
    """Test that labels.json has required vscodeclaude metadata."""

    def test_human_action_labels_have_vscodeclaude_metadata(self) -> None:
        """All human_action labels have required vscodeclaude fields."""
        from importlib import resources
        import json
        from pathlib import Path
        
        config_resource = resources.files("mcp_coder.config") / "labels.json"
        config_path = Path(str(config_resource))
        labels_config = json.loads(config_path.read_text(encoding="utf-8"))
        
        human_action_labels = [
            label for label in labels_config["workflow_labels"]
            if label["category"] == "human_action"
        ]
        
        assert len(human_action_labels) == 4
        
        required_fields = {"emoji", "display_name", "stage_short", "initial_command", "followup_command"}
        
        for label in human_action_labels:
            assert "vscodeclaude" in label, f"Missing vscodeclaude in {label['name']}"
            vscodeclaude = label["vscodeclaude"]
            assert set(vscodeclaude.keys()) == required_fields, f"Wrong fields in {label['name']}"
            
            # emoji should be non-empty string
            assert isinstance(vscodeclaude["emoji"], str) and vscodeclaude["emoji"]
            # display_name should be non-empty string
            assert isinstance(vscodeclaude["display_name"], str) and vscodeclaude["display_name"]
            # stage_short should be non-empty string
            assert isinstance(vscodeclaude["stage_short"], str) and vscodeclaude["stage_short"]
            # commands can be string or null
            assert vscodeclaude["initial_command"] is None or isinstance(vscodeclaude["initial_command"], str)
            assert vscodeclaude["followup_command"] is None or isinstance(vscodeclaude["followup_command"], str)

    def test_pr_created_has_null_commands(self) -> None:
        """status-10:pr-created should have null commands."""
        from importlib import resources
        import json
        from pathlib import Path
        
        config_resource = resources.files("mcp_coder.config") / "labels.json"
        config_path = Path(str(config_resource))
        labels_config = json.loads(config_path.read_text(encoding="utf-8"))
        
        pr_created = next(
            label for label in labels_config["workflow_labels"]
            if label["name"] == "status-10:pr-created"
        )
        
        assert pr_created["vscodeclaude"]["initial_command"] is None
        assert pr_created["vscodeclaude"]["followup_command"] is None
```

## VERIFICATION

After implementation:
1. Run: `pytest tests/workflows/vscodeclaude/test_types.py::TestLabelsJsonVscodeclaudeMetadata -v`
2. Verify JSON is valid: `python -c "import json; json.load(open('src/mcp_coder/config/labels.json'))"`
3. Existing tests should still pass: `pytest tests/workflows/vscodeclaude/test_types.py -v`
