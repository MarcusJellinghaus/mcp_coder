# Step 1: Add Failure Labels to labels.json + Update Tests

**Reference:** See `pr_info/steps/summary.md` for full context.

## LLM Prompt

> Implement Step 1 from `pr_info/steps/summary.md`.
> Add 5 failure status labels to `src/mcp_coder/config/labels.json` and update test expectations in `tests/cli/commands/test_set_status.py`.
> After making changes, run pylint, pytest (unit tests only), and mypy checks.

## WHERE

- `src/mcp_coder/config/labels.json` — add 5 entries to `workflow_labels` array
- `tests/cli/commands/test_set_status.py` — update `VALID_STATUS_LABELS` list and count assertion
- `tests/cli/commands/test_define_labels.py` — update count assertion `10` → `15`
- `tests/cli/commands/test_define_labels_label_changes.py` — update `created` count `9` → `14` and `call_count` `9` → `14` (two tests)

## WHAT

No new functions. Data-only changes to JSON config and test constants.

### labels.json — 5 new entries appended after `status-10:pr-created`

Each label follows this structure:
```json
{
  "internal_id": "<snake_case_id>",
  "name": "status-{N}f[-subtype]:{description}",
  "color": "<6-hex-no-hash>",
  "description": "<human-readable description>",
  "category": "human_action",
  "vscodeclaude": {
    "emoji": "<emoji>",
    "display_name": "<UPPER CASE NAME>",
    "stage_short": "<short_id>",
    "initial_command": null,
    "followup_command": null
  }
}
```

### Specific entries to add

1. `planning_failed` / `status-03f:planning-failed` / `b60205` / "Plan generation failed" / emoji: "❌" / display: "PLANNING FAILED" / stage_short: "plan-fail"
2. `implementing_failed` / `status-06f:implementing-failed` / `b60205` / "General implementation failure" / emoji: "❌" / display: "IMPLEMENTING FAILED" / stage_short: "impl-fail"
3. `ci_fix_needed` / `status-06f-ci:ci-fix-needed` / `d93f0b` / "CI exhausted fix attempts, needs manual intervention" / emoji: "🔧" / display: "CI FIX NEEDED" / stage_short: "ci-fail"
4. `llm_timeout` / `status-06f-timeout:llm-timeout` / `e99695` / "LLM API timeout during implementation" / emoji: "⏱️" / display: "LLM TIMEOUT" / stage_short: "timeout"
5. `pr_creating_failed` / `status-09f:pr-creating-failed` / `b60205` / "Pull request creation failed" / emoji: "❌" / display: "PR CREATION FAILED" / stage_short: "pr-fail"

### test_set_status.py changes

- Add the 5 new label names to `VALID_STATUS_LABELS` list
- Update `test_get_status_labels_from_config`: change `len(labels) == 10` → `len(labels) == 15`

### test_define_labels.py changes

- Update `test_define_labels_loads_config`: change `len(labels_config["workflow_labels"]) == 10` → `== 15`

### test_define_labels_label_changes.py changes

- `test_apply_labels_success_flow`: change `len(result["created"]) == 9` → `== 14` and `create_label.call_count == 9` → `== 14`
- `test_apply_labels_dry_run_mode`: change `len(result["created"]) == 9` → `== 14`

## HOW

- Edit `labels.json`: append 5 objects to the `workflow_labels` array (before the closing `]`)
- Edit `test_set_status.py`: extend `VALID_STATUS_LABELS` and fix count assertion

## DATA

No new data structures. Existing label schema is reused exactly.

## ALGORITHM

```
1. Open labels.json
2. Append 5 failure label objects to workflow_labels array
3. Open test_set_status.py
4. Add 5 failure label names to VALID_STATUS_LABELS
5. Change assertion from == 10 to == 15
6. Open test_define_labels.py, change count == 10 to == 15
7. Open test_define_labels_label_changes.py, change created count == 9 to == 14 and call_count == 9 to == 14 (two tests)
8. Run all quality checks
```
