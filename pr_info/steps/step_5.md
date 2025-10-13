# Step 5: Refactor define_labels.py to Use JSON Config

## LLM Prompt
```
Implement Step 5 from pr_info/steps/summary.md: Refactor define_labels.py to use the shared label_config module.

Follow Test-Driven Development:
1. Update tests for JSON config loading in define_labels workflow
2. Refactor define_labels.py to import load_labels_config() from workflows.label_config
3. Remove hard-coded WORKFLOW_LABELS constant
4. Ensure backward compatibility (same behavior, different data source)
5. Run all code quality checks using MCP tools

Use ONLY MCP filesystem tools for all file operations (mcp__filesystem__*).
Ensure define_labels.py continues to work exactly as before, just reading from JSON via shared module.
```

## WHERE: File Paths

### Files to MODIFY
```
workflows/define_labels.py                  # Refactor to use JSON config
tests/workflows/test_define_labels.py       # Update tests for JSON config
```

### Shared Code
Both `define_labels.py` and `issue_stats.py` use:
- Same JSON config file: `workflows/config/labels.json`
- Same loading function: `load_labels_config()` from `workflows/label_config.py`

## WHAT: Main Changes

### 1. Remove Hard-Coded Label Definitions
**Current (hard-coded):**
```python
WORKFLOW_LABELS = [
    {
        "name": "status-01:created",
        "color": "10b981",
        "description": "Fresh issue, may need refinement"
    },
    # ... more labels
]
```

**New (from JSON):**
```python
def load_labels_config(config_path: Path) -> dict:
    """Load label configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # Load from JSON instead of hard-coded constant
    config_path = project_dir.parent / "workflows" / "config" / "labels.json"
    labels_config = load_labels_config(config_path)
    workflow_labels = labels_config['workflow_labels']
```

### 2. Extract Workflow Labels from Config
The JSON has both `workflow_labels` and `ignore_labels`, but define_labels.py only needs `workflow_labels`.

```python
# Extract only the fields needed for GitHub label creation
labels_to_create = []
for label_config in labels_config['workflow_labels']:
    labels_to_create.append({
        'name': label_config['name'],
        'color': label_config['color'],
        'description': label_config['description']
    })
    # Note: 'internal_id' and 'category' not needed for GitHub API
```

## HOW: Integration Points

### Imports
```python
from pathlib import Path
from workflows.label_config import load_labels_config
# ... existing imports
```

### Usage in main()
```python
def main() -> None:
    """Main entry point for label definition workflow."""
    args = parse_arguments()
    setup_logging(args.log_level)
    project_dir = resolve_project_dir(args.project_dir)
    
    # Load labels from JSON config using shared module
    config_path = project_dir.parent / "workflows" / "config" / "labels.json"
    try:
        labels_config = load_labels_config(config_path)  # From workflows.label_config
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)
    
    # Extract workflow labels for GitHub API
    workflow_labels = labels_config['workflow_labels']
    
    # Rest of the workflow continues as before...
    labels_manager = LabelsManager(project_dir)
    # ...
```

## ALGORITHM: Main Workflow Changes

```
FUNCTION main():
    args = parse_arguments()
    setup_logging(args.log_level)
    project_dir = resolve_project_dir(args.project_dir)
    
    # NEW: Load from JSON instead of using hard-coded constant
    config_path = project_dir.parent / "workflows" / "config" / "labels.json"
    labels_config = load_labels_config(config_path)
    workflow_labels = labels_config['workflow_labels']
    
    # UNCHANGED: Rest of workflow
    labels_manager = LabelsManager(project_dir)
    
    IF args.dry_run:
        display_labels(workflow_labels, dry_run=True)
    ELSE:
        sync_labels(labels_manager, workflow_labels)
        display_labels(workflow_labels, dry_run=False)
```

## DATA: Backward Compatibility

### Before (Hard-Coded)
```python
WORKFLOW_LABELS = [
    {"name": "status-01:created", "color": "10b981", "description": "..."},
    # ... 9 more labels
]
```

### After (From JSON)
```python
# Load from JSON
config = load_labels_config(Path("workflows/config/labels.json"))
workflow_labels = config['workflow_labels']
# Each label has: name, color, description (+ internal_id, category which we ignore)
```

### Same Behavior
- Both produce identical list of labels for GitHub API
- Only difference: data source (JSON vs Python constant)
- JSON has extra fields (internal_id, category) that define_labels.py ignores

## Implementation Checklist
- [ ] Add import: `from workflows.label_config import load_labels_config`
- [ ] Remove WORKFLOW_LABELS constant
- [ ] Add `import json` for JSONDecodeError handling
- [ ] Update main() to load from JSON config
- [ ] Add error handling for missing/invalid JSON
- [ ] Extract only needed fields (name, color, description) from JSON
- [ ] Update tests to verify JSON loading works
- [ ] Add test for missing config file error
- [ ] Add test for invalid JSON error
- [ ] Verify backward compatibility (same labels created)
- [ ] Run all code quality checks

## Test Functions (test_define_labels.py)

### Updated Tests
```python
def test_main_uses_shared_label_config():
    """Test that main() uses load_labels_config from shared module"""
    # Mock workflows.label_config.load_labels_config
    # Verify it's called with correct path
    # Verify workflow_labels extracted correctly
    pass

def test_workflow_labels_extraction():
    """Test extracting workflow labels from config"""
    # Load config using shared module
    # Extract workflow_labels
    # Verify correct fields present for GitHub API
    pass
```

**Note:** Tests for `load_labels_config()` itself are in `tests/workflows/test_label_config.py` (created in Step 1)

### Integration Test
```python
def test_main_workflow_with_json_config():
    """Test main workflow reads from JSON config via shared module"""
    # Mock workflows.label_config.load_labels_config
    # Verify labels created from JSON, not hard-coded constant
    # Verify behavior identical to before refactoring
    pass
```

## Quality Checks
```python
# Fast unit tests:
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# Type checking:
mcp__code-checker__run_mypy_check()

# Code quality:
mcp__code-checker__run_pylint_check()
```

## Expected Test Output
```
tests/workflows/test_define_labels.py::test_load_labels_config_valid PASSED
tests/workflows/test_define_labels.py::test_load_labels_config_missing_file PASSED
tests/workflows/test_define_labels.py::test_load_labels_config_invalid_json PASSED
tests/workflows/test_define_labels.py::test_workflow_labels_extraction PASSED
tests/workflows/test_define_labels.py::test_main_workflow_with_json_config PASSED
... (existing tests should still pass)
```

## Manual Verification

### Test Label Creation Still Works
```bash
# Dry run mode (should display labels from JSON)
workflows\define_labels.bat --dry-run

# Actual run (should create labels from JSON)
workflows\define_labels.bat
```

**Verify:**
- Same 10 workflow labels displayed/created
- Labels have correct names, colors, descriptions
- No errors or warnings
- Behavior identical to before refactoring

## Notes
- **Single source of truth**: Both workflows now use same JSON config
- **Minimal changes**: Only change data source, not behavior
- **Backward compatibility**: define_labels.bat should work exactly as before
- **Error handling**: Clear messages if JSON missing or invalid
- **Ignore extra fields**: JSON has internal_id and category, which define_labels doesn't need
- **Future proof**: If we add more workflows, they all use the same label definitions
