# Step 1 — Add status-71..74 labels to labels.json

Reference: `pr_info/steps/summary.md` for the full architecture. This step
only adds the four new workflow labels; nothing executes them yet.

## Precondition check

Read `src/mcp_coder/config/labels.json` and
`tests/workflows/vscodeclaude/test_types.py`. If
`TestLabelsJsonVscodeclaudeMetadata.test_human_action_labels_have_vscodeclaude_metadata`
does not assert `len(human_action_labels) == 27`, or the `workflow_labels`
list in `labels.json` is not a flat list of dicts with
`internal_id`/`name`/`color`/`description`/`category` keys, write one line
to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/config/labels.json` (modify)
- `tests/workflows/vscodeclaude/test_types.py` (modify)

## WHAT

Four new entries appended to the `workflow_labels` array in `labels.json`,
in label-number order (after `status-10:pr-created`, before the `status-03f*`
failure entries — position doesn't matter functionally, but keep numeric
order for readability):

```json
{
  "internal_id": "merge_conflict",
  "name": "status-71:merge-conflict",
  "color": "fda4af",
  "description": "PR is no longer cleanly mergeable against its base",
  "category": "bot_pickup"
},
{
  "internal_id": "fixing_merge_conflict",
  "name": "status-72:fixing-merge-conflict",
  "color": "fb7185",
  "description": "Mechanical rebase in progress to resolve merge conflict (auto/in-progress)",
  "category": "bot_busy",
  "stale_timeout_minutes": 15
},
{
  "internal_id": "merge_conflict_failed",
  "name": "status-73:merge-conflict-failed",
  "color": "e99695",
  "description": "status-72 Jenkins job died without transitioning the label (crash watchdog)",
  "category": "human_action",
  "failure": true,
  "vscodeclaude": {
    "emoji": "⚠️",
    "display_name": "MERGE CONFLICT FAILED",
    "stage_short": "merge-conflict-fail",
    "commands": ["/check_branch_status"],
    "requires_branch": true,
    "color": "red"
  }
},
{
  "internal_id": "pr_merge_conflict",
  "name": "status-74:pr-merge-conflict",
  "color": "b60205",
  "description": "Rebase could not resolve the merge conflict - needs manual resolution",
  "category": "human_action",
  "failure": true,
  "vscodeclaude": {
    "emoji": "⚠️",
    "display_name": "PR MERGE CONFLICT",
    "stage_short": "pr-conflict",
    "commands": ["/check_branch_status"],
    "requires_branch": true,
    "color": "red"
  }
}
```

`status-71` and `status-72` intentionally have no `vscodeclaude` block —
same as every other `bot_pickup`/`bot_busy` label (e.g. `status-02`,
`status-03`).

## HOW

No code changes. `label_config.build_label_lookups()` and
`update_workflow_label()` read `labels.json` at call time, so later steps
can reference these four `internal_id`s immediately once this step lands.

## ALGORITHM

Not applicable — static config data.

## DATA

`labels.json`'s `human_action` category count goes from 27 to 29.

## TDD order

1. In `tests/workflows/vscodeclaude/test_types.py`, change
   `assert len(human_action_labels) == 27` to `== 29`. Run the test file —
   it must now fail against the current `labels.json`.
2. Add the four entries to `labels.json` as above.
3. Re-run the full test suite; the count assertion and the existing
   per-label `vscodeclaude` field checks in the same test must now pass
   (the new entries already carry `emoji`/`display_name`/`stage_short`).

## Checks before commit

Run pylint, pytest (fast unit marker set), mypy, and
`mcp__mcp-tools-py__run_format_code`. All must pass.

## Commit message

```
feat(labels): add status-71..74 merge-conflict labels
```

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for the overall design, then implement
> `pr_info/steps/step_1.md` exactly as written: update the label count
> assertion in `tests/workflows/vscodeclaude/test_types.py` first, confirm
> it fails, then add the four new label entries to
> `src/mcp_coder/config/labels.json`. If the precondition check in this
> step's "Precondition check" section fails, write one line to
> `pr_info/.blocked.txt` and stop. Otherwise make one commit containing the
> test change and the config change together, after formatters/pylint/
> pytest/mypy all pass.
