# Step 1: Add Tests for Workflow Label Removal

## LLM Prompt

```
Read pr_info/steps/summary.md for context on Issue #193.

This step adds tests BEFORE implementing the fix (TDD approach).

Implement the test changes described in this step file.
Run the tests to confirm they fail (expected - fix not yet implemented).
```

## WHERE

- **File:** `tests/utils/github_operations/test_issue_manager_label_update.py`

## WHAT

### 1. Update Existing Test: `test_update_workflow_label_missing_source_label`

Add assertion to verify no workflow labels remain after transition.

**Current behavior:** Test only verifies target label is added.
**New behavior:** Also verify no other workflow labels (like `status-05:plan-ready`) are present.

### 2. Add New Test: `test_update_workflow_label_removes_different_workflow_label`

Test the exact production bug scenario from Issue #192.

**Function signature:**
```python
def test_update_workflow_label_removes_different_workflow_label(
    self, mock_github: Mock, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
```

## HOW

- Follow existing test patterns in the file
- Use `MOCK_LABELS_CONFIG` fixture (already includes `status-05:plan-ready` as `plan_review`)
- Mock `get_issue` to return issue with wrong workflow label
- Assert `set_labels` is called with correct label set

## ALGORITHM (New Test)

```
1. Setup: Issue has ["status-05:plan-ready", "bug"] (wrong workflow label + non-workflow)
2. Call: update_workflow_label("implementing", "code_review")
3. Assert: set_labels called with issue_number=123
4. Assert: "status-07:code-review" in labels (target added)
5. Assert: "status-05:plan-ready" NOT in labels (wrong workflow removed)
6. Assert: "bug" in labels (non-workflow preserved)
```

## DATA

**Mock issue data for new test:**
```python
mock_issue_data: IssueData = {
    "number": 123,
    "title": "Test Issue",
    "body": "Test body",
    "state": "open",
    "labels": ["status-05:plan-ready", "bug"],  # Wrong workflow label present
    "assignees": [],
    "user": "testuser",
    "created_at": None,
    "updated_at": None,
    "url": "https://github.com/test/test/issues/123",
    "locked": False,
}
```

## EXPECTED TEST RESULT

- New test `test_update_workflow_label_removes_different_workflow_label`: **FAIL** (until Step 2)
- Updated test `test_update_workflow_label_missing_source_label`: May pass or fail depending on assertion placement

## Notes

- The `MOCK_LABELS_CONFIG` already includes the label `status-05:plan-ready` with internal_id `plan_review`
- No changes needed to mock configuration
