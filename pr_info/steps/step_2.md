# Step 2: Fix update_workflow_label Logic

## LLM Prompt

```
Read pr_info/steps/summary.md for context.
Implement the fix. Run tests to verify.
```

## File: `src/mcp_coder/utils/github_operations/issue_manager.py`

### Change 1: Add INFO log (before Step 8, ~line 365)

```python
if from_label_name not in current_labels:
    logger.info(
        f"Source label '{from_label_name}' not present on issue #{issue_number}. "
        "Proceeding with transition."
    )
```

### Change 2: Fix label removal logic (line ~372)

**From:**
```python
new_labels = (current_labels - {from_label_name}) | {to_label_name}
```

**To:**
```python
new_labels = (current_labels - label_lookups["all_names"]) | {to_label_name}
```

## Expected Result

All tests in `test_issue_manager_label_update.py` should **PASS**.
