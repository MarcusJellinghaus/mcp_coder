# Step 1 — Labels `merged` / `merge_failed`, `72` stale timeout, workflow-matrix cards

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **only** `pr_info/steps/step_1.md`.
> Follow TDD: update the tests first, then `labels.json` and the matrix HTML.
> Run format, pylint, mypy, pytest (fast unit set, `-n auto`) and make them pass.
> Produce exactly one commit.

## WHERE

- `src/mcp_coder/config/labels.json`
- `docs/processes-prompts/github_Issue_Workflow_Matrix.html`
- Tests that count or list labels: `tests/cli/commands/test_define_labels*.py`,
  `tests/config/test_label_config.py`, `tests/workflows/vscodeclaude/test_types.py`
  (search `tests/` for the current label total and for the ordered expected-names list;
  re-derive the numbers, do not trust any number in this file)

## WHAT

No Python code. Data only.

## DATA

Append both entries at the **end** of the `workflow_labels` array (after
`code_review_ci_unknown`, the last existing status label):

```json
{
  "internal_id": "merged",
  "name": "status-99:merged",
  "color": "0e8a16",
  "description": "PR merged automatically after CI passed",
  "category": "human_action",
  "vscodeclaude": {
    "emoji": "✅",
    "display_name": "MERGED",
    "stage_short": "merged"
  }
},
{
  "internal_id": "merge_failed",
  "name": "status-99f:merge-failed",
  "color": "b60205",
  "description": "CI green but the PR could not be merged automatically",
  "category": "human_action",
  "failure": true,
  "vscodeclaude": {
    "emoji": "🔀",
    "display_name": "MERGE FAILED",
    "stage_short": "merge-fail",
    "commands": ["/check_branch_status"],
    "requires_branch": true,
    "color": "red"
  }
}
```

Change `fixing_merge_conflict` (`status-72`) `stale_timeout_minutes`: `15` → `30`.

## HOW

- Tests first: bump every total-label count by 2, the `human_action` count in
  `tests/workflows/vscodeclaude/test_types.py` by 2, and append
  `"status-99:merged"`, `"status-99f:merge-failed"` to the ordered expected-names list.
  If a test asserts the `72` timeout, change it to 30.
- `tests/docs/test_workflow_matrix.py` requires a `label-card` with a `label-name` for every
  label, and for `merge_failed` its `/check_branch_status` inside the card's `auto-command`
  element. Add two cards to the matrix HTML, modelled on the `status-84` card (same markup):
  - `status-99:merged` — description as above, badge "Done", manual/exit line
    "issue done; closes on merge into default branch".
  - `status-99f:merge-failed` — `highlight-red`, `<div class="auto-command">&#x25b6; Auto: <code>/check_branch_status</code></div>`,
    manual/exit line "merge manually → close the issue", badge `badge-failed` "Failed".
  Place them in a new row "PR merge (auto_merge) — 99 / 99f" after the CI row.

## Precondition

If `tests/docs/test_workflow_matrix.py` does not exist or checks a different card
structure than described, write one line to `pr_info/.blocked.txt` and stop.

## Done when

All label / matrix / vscodeclaude tests pass with the new labels; nothing else changed.
