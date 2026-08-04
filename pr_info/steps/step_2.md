# Step 2 — Two new failure labels in `labels.json`

**Read first:** `pr_info/steps/summary.md` (§ "Two new failure labels"). This step
adds the label data both gates route to, plus the label-config tests, so that
Step 3's `failure_labels` entries resolve to real labels.

## WHERE

- **Modified:** `src/mcp_coder/config/labels.json`
- **Modified test:** `tests/config/test_label_config.py`
- **Modified test:** `tests/cli/commands/test_define_labels.py`

## WHAT — two label objects

Add after the existing `code_review_*` failure labels, mirroring the
`code_review_ci` block's full shape (`color`, `description`, `category`,
`failure`, and the complete `vscodeclaude` block — not just `commands`):

```jsonc
{
  "internal_id": "code_review_open_tasks",
  "name": "status-17f-tasks:code-review-open-tasks",
  "color": "d93f0b",
  "description": "Open implementation tasks remain — run /implementation_finalise",
  "category": "human_action",
  "failure": true,
  "vscodeclaude": {
    "emoji": "📋",
    "display_name": "CODE REVIEW OPEN TASKS",
    "stage_short": "code-review-open-tasks",
    "commands": ["/implementation_finalise"],
    "color": "red"
  }
},
{
  "internal_id": "code_review_ci_unknown",
  "name": "status-17f-ci-unknown:code-review-ci-undeterminable",
  "color": "d93f0b",
  "description": "Could not prove CI ran green during automated code review",
  "category": "human_action",
  "failure": true,
  "vscodeclaude": {
    "emoji": "❓",
    "display_name": "CODE REVIEW CI UNDETERMINABLE",
    "stage_short": "code-review-ci-unknown",
    "commands": ["/check_branch_status"],
    "color": "red"
  }
}
```

## HOW / integration points

- Placement in the JSON array matters: `test_define_labels.py` asserts the full
  label-name sequence. Append both new names to that `expected_names` list in the
  **same order** they appear in `labels.json`.

## TDD

1. **`tests/config/test_label_config.py`**:
   - Add both to `REVIEW_LABELS` (tuples `(internal_id, name, "human_action")`).
     Update the `test_review_labels_present` docstring: "13 review labels" → "15".
   - Add `code_review_ci_unknown` to `REVIEW_FAILURE_IDS` (its command *is*
     `/check_branch_status`, so `test_review_failure_labels_shape` passes as-is).
   - **Do not** add `code_review_open_tasks` to `REVIEW_FAILURE_IDS` — that
     parametrized test asserts `commands == ["/check_branch_status"]`, which would
     fail. Add a dedicated assertion instead:
     ```python
     def test_open_tasks_label_recovery_command() -> None:
         config = load_labels_config(get_labels_config_path(None))
         label = next(l for l in config["workflow_labels"]
                      if l["internal_id"] == "code_review_open_tasks")
         assert label["failure"] is True
         assert label["vscodeclaude"]["commands"] == ["/implementation_finalise"]
     ```
   - `test_review_labels_config_validates` (calls `validate_labels_config`) must
     still pass — confirm the new blocks satisfy the schema.
2. **`tests/cli/commands/test_define_labels.py`** — append the two new names to
   the `expected_names` sequence (in JSON order).

## DATA

Two additional entries in `config["workflow_labels"]`; no code consumes them yet.

## Checks

pylint / pytest / mypy green (label tests exercise the JSON).

## Commit

`Add code-review open-tasks and ci-undeterminable failure labels`
