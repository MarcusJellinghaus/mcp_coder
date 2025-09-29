# Step 3: Integration Tests for Label Operations

## Context
Create integration tests for label CRUD operations using real GitHub API. Tests written before implementation (TDD), will fail until Step 4.

## WHERE

### Test File
```
tests/utils/test_github_operations.py
```

Add new test class `TestLabelsManagerIntegration` after existing `TestPullRequestManagerIntegration` class.

## WHAT

### Test Class and Methods

```python
@pytest.mark.github_integration
class TestLabelsManagerIntegration:
    """Integration tests for LabelsManager with GitHub API."""
    
    def test_labels_lifecycle(self, labels_manager: LabelsManager) -> None
    def test_get_label_by_name(self, labels_manager: LabelsManager) -> None
    def test_create_label_idempotency(self, labels_manager: LabelsManager) -> None
```

### Fixture

```python
@pytest.fixture
def labels_manager(tmp_path: Path) -> Generator[LabelsManager, None, None]:
    """Create LabelsManager instance for testing."""
```

## HOW

### Fixture Integration Pattern
```python
# Same pattern as pr_manager fixture:
1. Get token from env or config
2. Get test repo URL from env or config
3. Clone test repository to tmp_path
4. Create LabelsManager instance
5. Yield for test
6. Cleanup handled by test
```

### Test Pattern
- Use timestamp in label names to avoid conflicts
- Create label, verify creation
- List labels, verify our label exists
- Delete label, verify deletion
- Use try/finally to ensure cleanup

## ALGORITHM

### Lifecycle Test Logic
```
1. Setup: Generate unique label name with timestamp
2. Create: Call create_label with test data
3. Assert: Verify label data returned correctly
4. Update: Call update_label to change color/description
5. Assert: Verify updated label data returned correctly
6. List: Call get_labels and find our label with updated data
7. Delete: Call delete_label with label name
8. Assert: Verify deletion successful (returns True)
9. Cleanup: Ensure label deleted in finally block
```

### Get Label Test Logic
```
1. Setup: Generate unique label name with timestamp
2. Create: Call create_label with test data
3. Assert: Verify label created successfully
4. Get Single: Call get_label with the label name
5. Assert: Verify returned LabelData matches created label
6. Get Nonexistent: Call get_label with nonexistent name
7. Assert: Verify empty dict {} returned (no exception)
8. Cleanup: Delete label in finally block
```

### Idempotency Test Logic
```
1. Setup: Generate unique label name with timestamp
2. Create: Call create_label with test data (first time)
3. Assert: Verify label created successfully
4. Create Again: Call create_label with same name (should succeed, not fail)
5. Assert: Verify same label returned, no error raised
6. Cleanup: Delete label in finally block
```

## DATA

### Test Data
```python
test_label_name = f"test-label-{timestamp}"
test_color = "FF5500"  # Orange (both "FF5500" and "#FF5500" work)
test_description = f"Test label created at {timestamp}"
updated_color = "00AA00"  # Green
updated_description = "Updated description"
```

### Expected Returns
- `create_label()`: `LabelData` dict with name, color, description, url
- `get_labels()`: `List[LabelData]` containing all labels
- `delete_label()`: `bool` (True on success)

## LLM Prompt

```
Implement integration tests for LabelsManager label operations.

Context: Read pr_info/steps/summary.md for overview.
Reference: tests/utils/test_github_operations.py -> pr_manager fixture and TestPullRequestManagerIntegration

Tasks:
1. Add labels_manager fixture following pr_manager pattern
2. Add TestLabelsManagerIntegration class with @pytest.mark.github_integration
3. Implement test_labels_lifecycle method as specified in pr_info/steps/step_3.md
4. Implement test_get_label_by_name to test get_label() method (get existing label and nonexistent label)
5. Implement test_create_label_idempotency to verify create succeeds when label exists
6. Use timestamp in label names to avoid conflicts: f"test-label-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
7. Ensure cleanup in finally block (delete test label)

Test structure:
- **Lifecycle test**: Create label with unique name, color FF5500, description
- Verify created label data structure
- List all labels and find our test label
- Delete the test label
- Verify deletion returns True
- **Get label test**: Create label, use get_label() to retrieve it by name
- Verify returned data matches created label
- Test get_label() with nonexistent name returns {}
- **Idempotency test**: Create label, then create again with same name
- Verify second create returns existing label without error
- Cleanup in finally block

Run: pytest tests/utils/test_github_operations.py::TestLabelsManagerIntegration -v -m github_integration
Expected: Tests FAIL (no implementation yet - TDD approach)
Note: Requires GitHub token and test_repo_url in config

Test count: 3 integration tests (lifecycle, get_label, idempotency)
```

## Notes

- Tests should FAIL initially (TDD red phase)
- Use `datetime.now().strftime('%Y%m%d-%H%M%S')` for unique names
- Always cleanup in finally block to avoid polluting test repo
- Skip tests gracefully if GitHub config missing
- Integration test requires real GitHub API access
