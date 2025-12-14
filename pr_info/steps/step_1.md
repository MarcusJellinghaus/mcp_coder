# Step 1: Add Tests for Workflow Label Removal

## LLM Prompt

```
Read pr_info/steps/summary.md for context on Issue #193.
Implement the test changes. Run tests — the new test will FAIL. This is expected (TDD). Proceed to Step 2.
```

## File: `tests/utils/github_operations/test_issue_manager_label_update.py`

### Add `test_update_workflow_label_removes_different_workflow_label`

Test the production bug scenario:

```python
def test_update_workflow_label_removes_different_workflow_label(
    self, mock_github: Mock, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Tests removal of unexpected workflow label during transition."""
```

**Setup:**
- Issue has `["status-05:plan-ready", "bug"]` (wrong workflow + non-workflow)

**Action:**
- Call `update_workflow_label("implementing", "code_review")`

**Assert:**
- `"status-07:code-review"` in labels (target added)
- `"status-05:plan-ready"` NOT in labels (wrong workflow removed)
- `"bug"` in labels (non-workflow preserved)

## Expected Result

New test will **FAIL** — this is expected. The fix is implemented in Step 2.
