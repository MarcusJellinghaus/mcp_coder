# Step 1: Add FailureCategory enum value, label entry, retry constant, and static prompt change

**References:** [summary.md](summary.md), Issue #711

## Overview

Foundation step: add the new `FailureCategory` enum value with its matching label in `labels.json`, add the retry budget constant, and strengthen the static prompt. These are all configuration/data changes with no logic — safe to bundle.

## WHERE

- `src/mcp_coder/workflows/implement/constants.py`
- `src/mcp_coder/config/labels.json`
- `src/mcp_coder/prompts/prompts.md`
- `tests/workflows/implement/test_constants.py`
- `tests/workflows/test_label_config.py`

## WHAT

### constants.py

Add to `FailureCategory` enum:
```python
NO_CHANGES_AFTER_RETRIES = "no_changes_after_retries"
```

Add module-level constant **adjacent to `RUN_MYPY_AFTER_EACH_TASK`** (the task-processing knobs section, NOT next to the CI retry constants below):
```python
# Used by the `implement` workflow's task-processing retry loop
# (process_task_with_retry in task_processing.py) to bound retries
# when an LLM call produces zero file changes for a task.
MAX_NO_CHANGE_RETRIES = 3  # Max LLM calls per task when zero changes detected
```

### labels.json

Add new label entry to `workflow_labels` array (after the existing `llm_timeout` entry):
```json
{
  "internal_id": "no_changes_after_retries",
  "name": "status-06f-nochange:no-changes-after-retries",
  "color": "d93f0b",
  "description": "LLM produced no file changes after multiple retry attempts",
  "category": "human_action",
  "vscodeclaude": {
    "emoji": "🔄",
    "display_name": "NO CHANGES AFTER RETRIES",
    "stage_short": "no-change",
    "commands": ["/check_branch_status"]
  }
}
```

### prompts.md

Add to the existing `**RULES:**` section of "Implementation Prompt Template using task tracker":
```
- If a sub-task is already complete (no code changes needed), STILL tick the box `[ ]` → `[x]`. Ticking the checkbox IS the required deliverable for that sub-task.
```

### test_constants.py

Add assertion in `test_values_match_label_ids`:
```python
assert FailureCategory.NO_CHANGES_AFTER_RETRIES.value == "no_changes_after_retries"
```

### test_label_config.py

Add `"no_changes_after_retries"` to the `ERROR_STATUS_IDS` list so the existing parametrized test validates the new label has a vscodeclaude block with commands.

## HOW

- Enum value follows existing pattern (string value = `labels.json` `internal_id`)
- Label follows existing failure label pattern (`status-06f-*`, `human_action` category, `commands: ["/check_branch_status"]`)
- Constant `MAX_NO_CHANGE_RETRIES` placed next to `RUN_MYPY_AFTER_EACH_TASK` (other task-processing knobs), with a comment noting it is consumed by the `implement` workflow's `process_task_with_retry` loop in `task_processing.py`

## DATA

- `FailureCategory.NO_CHANGES_AFTER_RETRIES.value` → `"no_changes_after_retries"`
- `MAX_NO_CHANGE_RETRIES` → `3`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1: Add the new FailureCategory enum value, MAX_NO_CHANGE_RETRIES constant, label entry, static prompt change, and test updates.

Files to modify:
- src/mcp_coder/workflows/implement/constants.py
- src/mcp_coder/config/labels.json
- src/mcp_coder/prompts/prompts.md
- tests/workflows/implement/test_constants.py
- tests/workflows/test_label_config.py

Follow the step file exactly. Run pylint, pytest, mypy after changes. Mark sub-tasks [x] in TASK_TRACKER.md.
```
