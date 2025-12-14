# Step 2: Fix update_workflow_label Logic

## LLM Prompt

```
Read pr_info/steps/summary.md for context on Issue #193.
Read pr_info/steps/step_1.md for the tests that were added.

This step implements the fix to make the tests pass.

Implement the code changes described in this step file.
Run all tests in test_issue_manager_label_update.py to verify the fix.
```

## WHERE

- **File:** `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Method:** `update_workflow_label()` (lines ~350-395)

## WHAT

### 1. Add INFO Log for Missing Source Label

**Location:** After Step 7 (idempotency check), before Step 8 (compute new labels)
**Around line:** 365-370

Log when source label is not present on the issue (helps debug workflow sequencing).

### 2. Fix Label Removal Logic

**Location:** Line 372 (Step 8 comment)

**Change FROM:**
```python
new_labels = (current_labels - {from_label_name}) | {to_label_name}
```

**Change TO:**
```python
new_labels = (current_labels - label_lookups["all_names"]) | {to_label_name}
```

## HOW

- `label_lookups` is already loaded at line ~340 (Step 4)
- `label_lookups["all_names"]` is a `set[str]` containing all workflow label names
- Set subtraction removes all workflow labels, preserving non-workflow labels
- Set union adds the target label

## ALGORITHM

```
1. current_labels = {"status-05:plan-ready", "bug"}  # from issue
2. all_workflow_labels = {"status-03:planning", "status-04:plan-review", 
                          "status-05:plan-ready", "status-06:implementing", 
                          "status-07:code-review", ...}
3. non_workflow_labels = current_labels - all_workflow_labels  # {"bug"}
4. new_labels = non_workflow_labels | {to_label_name}  # {"bug", "status-07:code-review"}
```

## DATA

**Input:** `label_lookups["all_names"]` - `set[str]` of all workflow label names
**Output:** `new_labels` - `set[str]` with exactly one workflow label + preserved non-workflow labels

## Code Changes

### Change 1: Add INFO log (insert after line ~365, before Step 8)

```python
# Log if source label is not present (helps debug workflow sequencing)
if from_label_name not in current_labels:
    logger.info(
        f"Source label '{from_label_name}' not present on issue #{issue_number}. "
        "Proceeding with transition."
    )
```

### Change 2: Fix line 372

```python
# Step 8: Compute new label set - remove ALL workflow labels, add target
new_labels = (current_labels - label_lookups["all_names"]) | {to_label_name}
```

## EXPECTED TEST RESULT

All tests in `test_issue_manager_label_update.py` should **PASS**, including:
- `test_update_workflow_label_removes_different_workflow_label` (new)
- `test_update_workflow_label_missing_source_label` (updated)
- All existing tests (unchanged behavior for normal cases)
