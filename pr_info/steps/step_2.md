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
def calculate_label_changes(
    existing_labels: list[tuple[str, str, str]],
    target_labels: list[tuple[str, str, str]]
) -> dict[str, list[str]]:
    """Pure function to calculate label changes without side effects.
    
    Args:
        existing_labels: List of (name, color, description) tuples from GitHub
        target_labels: List of (name, color, description) tuples to apply
    
    Returns:
        Dict with keys: 'created', 'updated', 'deleted', 'unchanged'
    """

def apply_labels(project_dir: Path, dry_run: bool = False) -> dict[str, list[str]]:
    """Apply workflow labels to repository.
    
    Args:
        project_dir: Path to project directory
        dry_run: If True, only preview changes without applying
    
    Returns:
        Dict with keys: 'created', 'updated', 'deleted', 'unchanged'
        Each value is list of label names
    """
```

### In `tests/workflows/test_define_labels.py`:
```python
# Pure function tests (no mocking needed)
def test_calculate_label_changes_empty_repo()
def test_calculate_label_changes_creates_new_labels()
def test_calculate_label_changes_updates_existing_labels()
def test_calculate_label_changes_deletes_obsolete_status_labels()
def test_calculate_label_changes_skips_unchanged_labels()
def test_calculate_label_changes_preserves_non_status_labels()
def test_calculate_label_changes_partial_match()
def test_calculate_label_changes_all_exist_unchanged()


# Integration tests (with mocked LabelsManager)
def test_apply_labels_success_flow(mock_labels_manager, tmp_path)
def test_apply_labels_dry_run_mode(mock_labels_manager, tmp_path)
def test_apply_labels_api_error_fails_fast(mock_labels_manager, tmp_path)
```

## HOW
- Import: `from pathlib import Path`
- Import: `from mcp_coder.utils.github_operations.labels_manager import LabelsManager`
- Import: `import logging`
- Use `@pytest.fixture` for mock_labels_manager
- Mock `get_labels()`, `create_label()`, `update_label()`, `delete_label()`

## ALGORITHM

### calculate_label_changes (pure function):
```
1. Initialize result dict with empty lists for 'created', 'updated', 'deleted', 'unchanged'
2. Build existing_map keyed by label name
3. For each target label:
   - If not in existing_map: add to 'created'
   - If in existing_map with same color/description: add to 'unchanged'
   - If in existing_map with different color/description: add to 'updated'
4. For each existing label starting with 'status-':
   - If not in target labels: add to 'deleted'
5. Return dict with all four categories
```

### apply_labels (orchestrator):
```
1. Initialize LabelsManager(project_dir)  # Validates token, repo connection
2. Get existing labels via get_labels()
3. Call calculate_label_changes(existing, WORKFLOW_LABELS)
4. If dry_run: log preview and return results
5. For each 'created': call create_label(), log action (INFO level)
6. For each 'updated': call update_label(), log action (INFO level)
7. For each 'deleted': call delete_label(), log action (INFO level)
8. For 'unchanged': skip API calls (idempotent), no logging
9. On any API error: stop immediately, fail fast with exit(1)
10. Return results dict
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
Reference: pr_info/steps/summary.md, pr_info/steps/step_1.md, pr_info/steps/decisions.md

Implement Step 2: apply_labels() function with comprehensive tests.

Tasks:
1. Implement calculate_label_changes() as pure function (NO logging, side-effect-free)
2. Write 8 unit tests for calculate_label_changes() covering:
   - Empty repo, create, update, delete, unchanged, preserve non-status
   - Partial match (5 of 10), all exist unchanged
3. Implement apply_labels() orchestrator with dry_run support
4. Add pytest fixtures in test file to mock LabelsManager (Option B from decisions)
5. Write 3 integration tests for apply_labels():
   - Success flow, dry-run mode, API error fails fast
6. Only apply_labels() logs (INFO level): "Created: status-01:created"
7. Skip API calls for unchanged labels (idempotency)
8. Strictly delete obsolete status-* labels
9. On API error: stop immediately (first error)
10. Run pytest to verify all tests pass

Follow separation of concerns: pure function for logic (no logging), orchestrator for side effects (logging, API calls).
```
