# Step 1: Add `stale_timeout_minutes` to labels.json Schema

## LLM Prompt
```
Implement Step 1 of Issue #340. Reference: pr_info/steps/summary.md

Add `stale_timeout_minutes` field to bot_busy labels in the configuration schema.
This enables configurable timeout thresholds for stale process detection.

Follow TDD: Write tests first, then implement.
```

---

## WHERE

| File | Action |
|------|--------|
| `tests/cli/commands/test_define_labels.py` | Add test class |
| `src/mcp_coder/config/labels.json` | Modify schema |

---

## WHAT

### Test: `TestStaleTimeoutConfiguration`

```python
class TestStaleTimeoutConfiguration:
    """Test stale_timeout_minutes field in labels configuration."""

    def test_bot_busy_labels_have_stale_timeout(self, labels_config_path: Path) -> None:
        """Test that all bot_busy labels have stale_timeout_minutes field."""
        
    def test_stale_timeout_values_are_positive_integers(self, labels_config_path: Path) -> None:
        """Test that stale_timeout_minutes values are positive integers."""
        
    def test_expected_timeout_values(self, labels_config_path: Path) -> None:
        """Test specific timeout values match requirements."""
```

---

## HOW

### Integration Points
- Uses existing `labels_config_path` fixture from `conftest.py`
- Uses existing `load_labels_config()` function

---

## DATA

### labels.json Changes

Add `stale_timeout_minutes` to these labels:

| Label | internal_id | Timeout (minutes) |
|-------|-------------|-------------------|
| `status-03:planning` | `planning` | 15 |
| `status-06:implementing` | `implementing` | 120 | (changed from previous 60) |
| `status-09:pr-creating` | `pr_creating` | 15 |

### Expected JSON Structure
```json
{
  "internal_id": "planning",
  "name": "status-03:planning",
  "color": "a7f3d0",
  "description": "Implementation plan being drafted (auto/in-progress)",
  "category": "bot_busy",
  "stale_timeout_minutes": 15
}
```

---

## VERIFICATION

```bash
# Run tests
pytest tests/cli/commands/test_define_labels.py::TestStaleTimeoutConfiguration -v

# Verify JSON is valid
python -c "import json; json.load(open('src/mcp_coder/config/labels.json'))"
```
