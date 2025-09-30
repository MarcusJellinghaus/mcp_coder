# Step 2: Implement apply_labels Core Function with Tests

## Objective
Create the core `apply_labels()` function that creates/updates/deletes labels using `LabelsManager`.

## Context
Reference `summary.md` and step_1.md. This step implements the main logic with comprehensive tests using mocks.

## WHERE
- Modify: `workflows/define_labels.py`
- Modify: `tests/workflows/test_define_labels.py`

## WHAT

### In `workflows/define_labels.py`:
```python
def apply_labels(project_dir: Path) -> dict[str, list[str]]:
    """Apply workflow labels to repository.
    
    Returns:
        Dict with keys: 'created', 'updated', 'deleted', 'unchanged'
        Each value is list of label names
    """
```

### In `tests/workflows/test_define_labels.py`:
```python
def test_apply_labels_creates_new_labels(mock_labels_manager, tmp_path)
def test_apply_labels_updates_existing_labels(mock_labels_manager, tmp_path)
def test_apply_labels_deletes_obsolete_status_labels(mock_labels_manager, tmp_path)
def test_apply_labels_skips_unchanged_labels(mock_labels_manager, tmp_path)
def test_apply_labels_preserves_non_status_labels(mock_labels_manager, tmp_path)
```

## HOW
- Import: `from pathlib import Path`
- Import: `from mcp_coder.utils.github_operations.labels_manager import LabelsManager`
- Import: `import logging`
- Use `@pytest.fixture` for mock_labels_manager
- Mock `get_labels()`, `create_label()`, `update_label()`, `delete_label()`

## ALGORITHM
```
1. Initialize LabelsManager(project_dir)
2. Get all existing labels via get_labels()
3. For each WORKFLOW_LABELS entry:
   - If exists and matches: track as 'unchanged'
   - If exists but differs: update_label(), track as 'updated'
   - If not exists: create_label(), track as 'created'
4. For each existing label starting with 'status-':
   - If not in WORKFLOW_LABELS: delete_label(), track as 'deleted'
5. Return categorized results dict
```

## DATA
- **Input**: `project_dir: Path`
- **Output**: `dict[str, list[str]]`
  ```python
  {
      "created": ["status-01:created", ...],
      "updated": ["status-05:plan-ready", ...],
      "deleted": ["status-99:old", ...],
      "unchanged": ["status-02:awaiting-planning", ...]
  }
  ```

## LLM Prompt
```
Reference: pr_info/steps/summary.md, pr_info/steps/step_1.md

Implement Step 2: apply_labels() function with tests.

Tasks:
1. Add pytest fixtures in tests/workflows/test_define_labels.py to mock LabelsManager
2. Write 5 tests covering create/update/delete/unchanged/preserve scenarios
3. Implement apply_labels() in workflows/define_labels.py
4. Use logger.info() to report each operation (create/update/delete)
5. Ensure obsolete status-* labels are deleted but other labels are preserved
6. Run pytest to verify all tests pass

Follow mocking patterns from tests/utils/github_operations/.
```
