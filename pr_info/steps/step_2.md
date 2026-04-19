# Step 2: Config validation (`validate_labels_config`)

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 2: Add `validate_labels_config()` function to `label_config.py` with tests. This function validates `default`, `promotable`, and `failure` field constraints. Write tests first (TDD), then implement. Run all code quality checks after changes.

## WHERE

- `src/mcp_coder/utils/github_operations/label_config.py` — add `validate_labels_config()`
- `tests/workflows/test_label_config.py` — add validation tests

## WHAT

### New function in `label_config.py`

```python
def validate_labels_config(labels_config: Dict[str, Any]) -> None:
    """Validate label config constraints. Raises ValueError on problems.
    
    Checks:
    1. Exactly one label has "default": true
    2. Each "promotable": true label has a next label in workflow_labels list
    3. No promotable label's next target has "failure": true
    """
```

**Return:** `None` on success, raises `ValueError` with descriptive message on failure.

## HOW

- Add function to `label_config.py` after `build_label_lookups()`
- Export it in the module (no `__all__` used, so just define it)
- No callers yet — `define_labels.py` will call it in Step 5

## ALGORITHM

```
labels = config["workflow_labels"]
defaults = [l for l in labels if l.get("default")]
if len(defaults) != 1: raise ValueError

for i, label in enumerate(labels):
    if label.get("promotable"):
        if i + 1 >= len(labels): raise ValueError("no next label")
        if labels[i + 1].get("failure"): raise ValueError("target is failure")
```

## DATA

- Input: `Dict[str, Any]` — the loaded labels config (same structure as `load_labels_config` returns)
- Output: `None` or raises `ValueError`

## Tests (TDD — write first)

Add to `tests/workflows/test_label_config.py`:

```python
class TestValidateLabelsConfig:
    def test_valid_config_passes(self):
        """Bundled config should pass validation."""
        
    def test_missing_default_raises(self):
        """Config with no default: true label raises ValueError."""
        
    def test_multiple_defaults_raises(self):
        """Config with two default: true labels raises ValueError."""
        
    def test_promotable_without_next_raises(self):
        """Last label in list with promotable: true raises ValueError."""
        
    def test_promotable_targeting_failure_raises(self):
        """Promotable label whose next entry has failure: true raises ValueError."""
        
    def test_valid_promotable_passes(self):
        """Promotable label with valid non-failure next entry passes."""

    def test_config_without_new_fields_fails(self):
        """Config missing default field fails validation (exactly one required)."""
```

Each test constructs a minimal `{"workflow_labels": [...]}` dict inline.

## Verification

- 7+ new tests pass
- Existing tests unaffected
- Pylint, mypy, pytest all green
