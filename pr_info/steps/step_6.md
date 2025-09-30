# Step 6: Integration Testing and Documentation

## Objective
Add integration test and verify complete workflow.

## Context
Reference `summary.md`. Final validation step.

## WHERE
- Modify: `tests/workflows/test_define_labels.py`
- Optionally: Add usage notes to README

## WHAT

### In `tests/workflows/test_define_labels.py`:
```python
def test_define_labels_integration(tmp_path):
    """Integration test verifying full workflow with real LabelsManager."""
    # This test can be marked @pytest.mark.integration
    # and skipped in CI if GitHub token not available
```

## HOW
- Use `pytest.mark.integration` decorator
- Test requires GitHub token in environment
- Verify script can be imported and executed
- Check all 10 labels are correctly defined

## ALGORITHM
```
Integration test:
1. Check if GitHub token available
2. Skip test if not (pytest.skip)
3. Run define_labels script on real repository
4. Verify results dict contains expected counts
5. Query GitHub API to confirm labels exist
```

## DATA
- **Test markers**: `@pytest.mark.integration`
- **Environment**: Requires `GITHUB_TOKEN`
- **Verification**: Check label names, colors, descriptions match spec

## LLM Prompt
```
Reference: pr_info/steps/summary.md, pr_info/steps/step_1-5.md

Implement Step 6: Integration test and final verification.

Tasks:
1. Add test_define_labels_integration() in tests/workflows/test_define_labels.py
2. Mark with @pytest.mark.integration
3. Skip if GITHUB_TOKEN not available
4. Test full workflow execution
5. Run all tests: pytest tests/workflows/test_define_labels.py -v
6. Run integration test manually if GitHub access available
7. Verify script works: python workflows/define_labels.py --project-dir . --log-level DEBUG

Final validation complete.
```
