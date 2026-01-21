# Step 2: Simplify Test Fixtures

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 2.

Simplify the labels_config_path fixtures in both test conftest files to use 
get_labels_config_path() directly instead of checking for the now-deleted 
workflows/config/labels.json.

Files to modify:
1. tests/conftest.py
2. tests/workflows/conftest.py

Both have identical fixtures that need the same simplification.
```

## WHERE

```
tests/conftest.py              <- MODIFY labels_config_path fixture
tests/workflows/conftest.py    <- MODIFY labels_config_path fixture
```

## WHAT

Simplify `labels_config_path()` fixture in both files.

### Current Signature - tests/conftest.py
```python
@pytest.fixture
def labels_config_path() -> Path:
    """Get the path to the labels configuration file."""
    from mcp_coder.utils.github_operations.label_config import get_labels_config_path
    
    conftest_path = Path(__file__).resolve()
    project_root = conftest_path.parent.parent  # tests/ -> project root
    
    # Check if running in development mode (workflows/config exists)
    local_config = project_root / "workflows" / "config" / "labels.json"
    if local_config.exists():
        return local_config
    
    return get_labels_config_path()
```

### Current Signature - tests/workflows/conftest.py
```python
@pytest.fixture
def labels_config_path() -> Path:
    """Get the path to the labels configuration file."""
    from mcp_coder.utils.github_operations.label_config import get_labels_config_path
    
    conftest_path = Path(__file__).resolve()
    project_root = conftest_path.parent.parent.parent  # tests/workflows/ -> project root
    
    # Check if running in development mode (workflows/config exists)
    local_config = project_root / "workflows" / "config" / "labels.json"
    if local_config.exists():
        return local_config
    
    return get_labels_config_path()
```

### New Signature (both files)
```python
@pytest.fixture
def labels_config_path() -> Path:
    """Get the path to the labels configuration file."""
    from mcp_coder.utils.github_operations.label_config import get_labels_config_path
    return get_labels_config_path()
```

## HOW

Edit both files to remove:
1. `conftest_path` variable
2. `project_root` variable  
3. `local_config` variable
4. The `if local_config.exists()` check

Keep only the import and direct call to `get_labels_config_path()`.

## ALGORITHM

```
1. Read tests/conftest.py
2. Replace labels_config_path fixture with simplified version
3. Read tests/workflows/conftest.py
4. Replace labels_config_path fixture with simplified version
5. Verify both files have consistent simplified fixtures
```

## DATA

**Return value**: `Path` to `src/mcp_coder/config/labels.json` (bundled config)

No change to return type or behavior - the function `get_labels_config_path()` already returns the bundled config when no local override exists.

## Verification

Run tests that use the fixture:
```bash
pytest tests/workflows/test_label_config.py -v
pytest tests/workflows/test_validate_labels.py -v
```
