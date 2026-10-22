# Summary — #1265: shorten `status-17f-ci-unknown` label name, validate GitHub label limits

## Problem

`status-17f-ci-unknown:code-review-ci-undeterminable` is 51 characters; GitHub caps
label names at 50, so `define-labels` gets a 422 on it and the label cannot exist.
`validate_labels_config()` does not check GitHub field limits, so such a name only
surfaces mid-sync.

## Architectural / design changes

- **No structural change.** No new modules, classes, or public symbols.
- **Data change:** one label `name` in the bundled `labels.json` is renamed to
  `status-17f-ci-unknown:code-review-ci-unknown` (44 chars). `internal_id`
  (`code_review_ci_unknown`), `display_name` and `stage_short` are unchanged; code
  references the label only by `internal_id`, so no code paths change.
- **Validation contract extended:** `validate_labels_config()` gains two checks per
  `workflow_labels` entry — `name` ≤ 50 chars, `description` ≤ 100 chars (read via
  `.get("description", "")`). Each raises `ValueError` naming `internal_id`, length,
  and limit.
- **Behaviour change:** because `define-labels` calls the validator before any GitHub
  API call, an over-long name/description in a bundled *or custom* config now stops
  the sync before anything is written (same as the existing default/promotable errors).
- Limits are inline literals (`50`, `100`) — KISS; the error message states them.

## Step order

Step 1 (rename) must land before step 2 (validator): the bundled config is validated
by `test_valid_config_passes`, which would fail on the 51-char name.

## Files modified

| File | Step | Change |
|------|------|--------|
| `src/mcp_coder/config/labels.json` | 1 | rename label `name` |
| `tests/cli/commands/test_define_labels.py` | 1 | update expected name |
| `tests/config/test_label_config.py` | 1, 2 | update expected name (1); add length tests (2) |
| `docs/processes-prompts/development-process.md` | 1 | update label name in table |
| `docs/processes-prompts/github_Issue_Workflow_Matrix.html` | 1 | update `label-name` div |
| `docs/cli-reference.md` | 1 | update label name |
| `src/mcp_coder/config/label_config.py` | 2 | length checks in `validate_labels_config()` |

No files or folders are created (besides these `pr_info/steps/` plan files).
