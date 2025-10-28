# Step 1: Label Configuration Integration

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.
**Decisions:** See `pr_info/steps/decisions.md` for architectural decisions.
**Prerequisites:** Step 0 must be complete (`build_label_lookups()` available in `label_config.py`).

## Objective
Integrate existing `build_label_lookups()` function from shared module to support label filtering in coordinator.

## WHERE

**Implementation File:**
- `src/mcp_coder/cli/commands/coordinator.py`
- Import `build_label_lookups` from shared module
- Use in `get_eligible_issues()` function

## WHAT

### Import Statement

```python
# In coordinator.py imports section
from workflows.label_config import load_labels_config, build_label_lookups
```

### Usage in get_eligible_issues()

```python
def get_eligible_issues(
    issue_manager: IssueManager,
    log_level: str = "INFO"
) -> list[IssueData]:
    """Get issues ready for automation, sorted by priority."""
    
    # Load and parse label configuration
    config_path = Path(__file__).parent.parent.parent.parent / "workflows" / "config" / "labels.json"
    labels_config = load_labels_config(config_path)
    label_lookups = build_label_lookups(labels_config)
    
    # Extract needed label sets
    bot_pickup_labels = {
        name for name, category in label_lookups["name_to_category"].items()
        if category == "bot_pickup"
    }
    ignore_labels = set(labels_config.get("ignore_labels", []))
    
    # ... rest of filtering logic ...
```

## HOW

### Integration Points

**Imports:**
```python
from pathlib import Path
from workflows.label_config import load_labels_config, build_label_lookups
```

**Path Construction:**
```python
# In get_eligible_issues()
config_path = Path(__file__).parent.parent.parent.parent / "workflows" / "config" / "labels.json"
```

## ALGORITHM

```
1. Construct path to workflows/config/labels.json
2. Load config using load_labels_config(config_path)
3. Build lookups using build_label_lookups(labels_config)
4. Extract bot_pickup labels from name_to_category dict
5. Extract ignore_labels from config
6. Use these sets in filtering logic
```

## DATA

### LabelLookups Structure (from build_label_lookups)
```python
LabelLookups = TypedDict('LabelLookups', {
    'id_to_name': dict[str, str],
    'all_names': set[str],
    'name_to_category': dict[str, str],  # <-- We use this
    'name_to_id': dict[str, str]
})
```

### Example Usage
```python
label_lookups = build_label_lookups(labels_config)

# Extract bot_pickup labels
bot_pickup_labels = {
    name for name, category in label_lookups["name_to_category"].items()
    if category == "bot_pickup"
}
# Result: {"status-02:awaiting-planning", "status-05:plan-ready", "status-08:ready-pr"}

# Extract ignore_labels
ignore_labels = set(labels_config.get("ignore_labels", []))
# Result: {"Overview"}
```

## Implementation Notes

1. **Reuse:** Don't reimplement - use existing `build_label_lookups()` from Step 0
2. **Path Resolution:** Use `Path(__file__)` for robust path construction
3. **Error Handling:** `load_labels_config()` and `build_label_lookups()` handle errors
4. **Simplicity:** Just import, call, and extract needed data

## LLM Prompt for Implementation

```
Implement Step 1 of the coordinator run feature as described in pr_info/steps/summary.md.

See pr_info/steps/decisions.md for architectural decisions.
Prerequisite: Step 0 must be complete (build_label_lookups available in label_config.py).

Task: Integrate label configuration in coordinator.py

Requirements:
1. Add import in src/mcp_coder/cli/commands/coordinator.py:
   from workflows.label_config import load_labels_config, build_label_lookups

2. In get_eligible_issues() function (Step 2):
   - Construct path to labels.json
   - Call load_labels_config(config_path)
   - Call build_label_lookups(labels_config)
   - Extract bot_pickup labels from name_to_category
   - Extract ignore_labels from config
   - Use these in filtering logic

3. No new tests needed - using existing shared functions

4. Run code quality checks:
   - mcp__code-checker__run_pylint_check
   - mcp__code-checker__run_mypy_check

Follow step_1.md. Use existing shared functionality - don't reimplement.
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

- ✅ Import statement added correctly
- ✅ Label configuration integrated in get_eligible_issues()
- ✅ Uses shared build_label_lookups() function
- ✅ Pylint/mypy checks pass
- ✅ Code follows existing coordinator.py style
- ✅ No code duplication
