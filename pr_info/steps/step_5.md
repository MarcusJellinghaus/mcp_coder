# Step 5 — Update `update_workflow_label` call sites

> **Reference**: See `pr_info/steps/summary.md` for full context (Issue #833, part 5 of 5).

## Goal

Switch the 4 call sites that use `issue_manager.update_workflow_label(...)` to call the standalone function `update_workflow_label(issue_manager, ...)` from `mcp_coder.workflow_utils.label_transitions`.

## WHERE

4 files with call sites:

1. `src/mcp_coder/workflows/create_plan/core.py` (~line 708)
2. `src/mcp_coder/workflows/create_pr/core.py` (~line 665)
3. `src/mcp_coder/workflows/implement/core.py` (~line 801)
4. `src/mcp_coder/workflow_utils/failure_handling.py` (~line 123)

## WHAT

### Change pattern

**Before:**
```python
issue_manager.update_workflow_label(
    from_label_id="implementing",
    to_label_id="code_review",
    validated_issue_number=issue_number,
)
```

**After:**
```python
from mcp_coder.workflow_utils.label_transitions import update_workflow_label

update_workflow_label(
    issue_manager,
    from_label_id="implementing",
    to_label_id="code_review",
    validated_issue_number=issue_number,
)
```

### Per-file details

**1. `workflows/create_plan/core.py`**
- Add import: `from mcp_coder.workflow_utils.label_transitions import update_workflow_label`
- Change: `issue_manager.update_workflow_label(...)` → `update_workflow_label(issue_manager, ...)`
- Label transition: `planning` → `plan_review`

**2. `workflows/create_pr/core.py`**
- The call site uses a lazy import of `IssueManager` (line ~662). Keep the lazy import for `IssueManager`, add import of `update_workflow_label` at top level.
- Change: `issue_manager.update_workflow_label(...)` → `update_workflow_label(issue_manager, ...)`
- Label transition: `pr_creating` → `pr_created`

**3. `workflows/implement/core.py`**
- Add import: `from mcp_coder.workflow_utils.label_transitions import update_workflow_label`
- Change: `issue_manager.update_workflow_label(...)` → `update_workflow_label(issue_manager, ...)`
- Label transition: `implementing` → `code_review`

**4. `workflow_utils/failure_handling.py`**
- Add import: `from mcp_coder.workflow_utils.label_transitions import update_workflow_label`
- Change: `issue_manager.update_workflow_label(...)` → `update_workflow_label(issue_manager, ...)`
- Label transition: `from_label_id` → `failure.category`

## ALGORITHM

No algorithm — call site updates only.

## DATA

No data structure changes. Same parameters, same return value.

## Commit

```
refactor: switch to standalone update_workflow_label
```

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement step 5 from pr_info/steps/step_5.md.

Update 4 call sites to use the standalone update_workflow_label function.
The function signature takes issue_manager as first arg, all other args are the same.
Run all checks (pylint, mypy, pytest unit tests) after implementation.
```
