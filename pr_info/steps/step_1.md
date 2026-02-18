# Step 1 — Add regression test for bundled labels.json loading

> TDD first: write the failing test that proves the bug and validates the fix.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Add a regression test to `tests/workflows/test_label_config.py` that verifies
the bundled `labels.json` is loadable via `importlib.resources` (i.e. without
relying on a real filesystem path).

The test must:
- Call `get_labels_config_path(None)` to obtain the bundled resource reference
- Pass the result directly to `load_labels_config()`
- Assert the returned dict has a non-empty `workflow_labels` list
- Assert every item in `workflow_labels` has the keys: internal_id, name, color,
  description, category

Import `get_labels_config_path` alongside the existing `load_labels_config` import.

Do NOT modify any source files in this step — only the test file.
```

---

## WHERE

- **File**: `tests/workflows/test_label_config.py`

## WHAT

New test function to add:

```python
def test_load_bundled_labels_config() -> None:
```

Add to existing imports:
```python
from mcp_coder.utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
)
```

## HOW

- No new imports from outside the existing test file pattern
- Uses `get_labels_config_path(None)` — the existing public API for the bundled case
- This test will **fail before the fix** (Step 2) because `get_labels_config_path(None)`
  currently returns `Path(str(Traversable))` which may not exist

## ALGORITHM

```
1. Call get_labels_config_path(None) → bundled_ref
2. Call load_labels_config(bundled_ref) → config
3. Assert config["workflow_labels"] is a non-empty list
4. For each label in config["workflow_labels"]:
       Assert required keys present: internal_id, name, color, description, category
5. Assert config["ignore_labels"] is a list
```

## DATA

- Input: none (no parameters)
- Output: none (assertions only)
- `config` type: `Dict[str, Any]` with keys `workflow_labels` (list) and `ignore_labels` (list)
