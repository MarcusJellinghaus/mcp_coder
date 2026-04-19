# Step 1: Add `default`, `promotable`, `failure` fields to label config

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 1: Add three new boolean fields to `labels.json`, update the schema documentation, and update the test fixture. Run all code quality checks after changes.

## WHERE

- `src/mcp_coder/config/labels.json` — production config
- `src/mcp_coder/config/labels_schema.md` — schema documentation
- `tests/workflows/config/test_labels.json` — test fixture

## WHAT

No new functions. Data-only changes to JSON and Markdown files.

### `labels.json` field additions

| Field | Type | Applied to |
|-------|------|------------|
| `"default": true` | bool | `created` label only (1 entry) |
| `"promotable": true` | bool | `created`, `plan_review`, `code_review` (3 entries) |
| `"failure": true` | bool | 9 failure labels: `planning_failed`, `planning_prereq_failed`, `planning_llm_timeout`, `implementing_failed`, `task_tracker_prep_failed`, `ci_fix_needed`, `llm_timeout`, `no_changes_after_retries`, `pr_creating_failed` |

### `labels_schema.md` additions

Add 3 rows to the "Per-label Fields" table:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `default` | bool | no | Exactly one label must have `"default": true`. Used as the initial label for new issues. |
| `promotable` | bool | no | Labels eligible for `/approve` promotion. Target is the next label in `workflow_labels` list. |
| `failure` | bool | no | Marks failure state labels. Promotable labels cannot target failure labels. |

### `test_labels.json` updates

Add `"default": true` to the `created` entry. Add `"promotable": true` to `created` and `plan_review`. Add a failure label entry for test coverage (e.g., add a `planning_failed` entry with `"failure": true`).

## HOW

Direct JSON edits. No imports or integration points.

## ALGORITHM

N/A — data-only step.

## DATA

The `labels.json` entries gain optional boolean fields. Omitted = `false`. Example:

```json
{
  "internal_id": "created",
  "name": "status-01:created",
  "color": "10b981",
  "description": "Fresh issue, may need refinement",
  "category": "human_action",
  "default": true,
  "promotable": true,
  ...
}
```

## Tests

Existing test `test_load_bundled_labels_config` in `tests/workflows/test_label_config.py` will implicitly verify the JSON is still loadable. No new tests in this step — validation logic tests come in Step 2.

## Verification

- All existing tests pass (the new fields are optional, so no breakage)
- Pylint, mypy, pytest all green
