# Step 1: Add label, enum member, and tests

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: Add the `task_tracker_prep_failed` label to `labels.json`, add the `TASK_TRACKER_PREP_FAILED` enum member to `FailureCategory`, and update the tests. Follow TDD — update tests first, then production code. Run all three code quality checks after changes. Commit as a single commit.

## WHERE

- `tests/workflows/implement/test_constants.py` — add enum assertion (test first)
- `tests/workflows/test_label_config.py` — add to `ERROR_STATUS_IDS` list (test first)
- `src/mcp_coder/config/labels.json` — add label entry
- `src/mcp_coder/workflows/implement/constants.py` — add enum member

## WHAT

### 1. Test: `test_constants.py` — `test_values_match_label_ids`

Add one assertion line to the existing test:

```python
assert FailureCategory.TASK_TRACKER_PREP_FAILED.value == "task_tracker_prep_failed"
```

### 2. Test: `test_label_config.py` — `ERROR_STATUS_IDS`

Add `"task_tracker_prep_failed"` to the existing list:

```python
ERROR_STATUS_IDS = [
    "planning_failed",
    "implementing_failed",
    "ci_fix_needed",
    "llm_timeout",
    "pr_creating_failed",
    "task_tracker_prep_failed",  # <-- new
]
```

### 3. Production: `labels.json`

Add new entry after `implementing_failed`:

```json
{
    "internal_id": "task_tracker_prep_failed",
    "name": "status-06f-prep:task-tracker-prep-failed",
    "color": "b60205",
    "description": "Task tracker preparation failed",
    "category": "human_action",
    "vscodeclaude": {
        "emoji": "❌",
        "display_name": "TASK TRACKER PREP FAILED",
        "stage_short": "prep-fail",
        "commands": ["/check_branch_status"]
    }
}
```

### 4. Production: `constants.py` — `FailureCategory` enum

Add one member:

```python
TASK_TRACKER_PREP_FAILED = "task_tracker_prep_failed"
```

## HOW

- No new imports, no new files, no integration changes.
- The enum value must exactly match the `internal_id` in `labels.json`.

## DATA

- `FailureCategory.TASK_TRACKER_PREP_FAILED.value` → `"task_tracker_prep_failed"`
- Label name: `"status-06f-prep:task-tracker-prep-failed"`

## Verification

Run all three checks:
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` (with `-m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"`)
- `mcp__tools-py__run_mypy_check`
