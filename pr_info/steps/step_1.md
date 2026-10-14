# Step 1 — Add the 4 CI-health labels

See [summary.md](./summary.md) for full context.

## Precondition

`src/mcp_coder/config/labels.json`'s `workflow_labels` array currently has
exactly 41 entries (the count the two tests below assert today). If it does
not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/config/labels.json` (modify)
- `tests/cli/commands/test_define_labels.py` (modify)
- `tests/cli/commands/test_define_labels_label_changes.py` (modify)

## WHAT

No new functions. Pure data: 4 new entries in the `workflow_labels` array,
appended after the existing `status-74:pr-merge-conflict` entry (the sibling
#1212 labels), mirroring their shape exactly.

```json
{
  "internal_id": "failing_ci",
  "name": "status-81:failing-ci",
  "color": "fda4af",
  "description": "PR's CI is failing and mergeable (conflict checked first)",
  "category": "bot_pickup"
},
{
  "internal_id": "fixing_ci",
  "name": "status-82:fixing-ci",
  "color": "fb7185",
  "description": "CI auto-fix loop in progress (auto/in-progress)",
  "category": "bot_busy",
  "stale_timeout_minutes": 120
},
{
  "internal_id": "ci_fix_failed",
  "name": "status-83:ci-fix-failed",
  "color": "e99695",
  "description": "status-82 Jenkins job died without transitioning the label (crash watchdog)",
  "category": "human_action",
  "failure": true,
  "vscodeclaude": {
    "emoji": "⚠️",
    "display_name": "CI FIX FAILED",
    "stage_short": "ci-fix-fail",
    "commands": ["/check_branch_status"],
    "requires_branch": true,
    "color": "red"
  }
},
{
  "internal_id": "pr_ci_failed",
  "name": "status-84:pr-ci-failed",
  "color": "b60205",
  "description": "CI auto-fix loop exhausted or hit an LLM failure - needs manual fix",
  "category": "human_action",
  "failure": true,
  "vscodeclaude": {
    "emoji": "⚠️",
    "display_name": "PR CI FAILED",
    "stage_short": "pr-ci-fail",
    "commands": ["/check_branch_status"],
    "requires_branch": true,
    "color": "red"
  }
}
```

## HOW

No code integration — `config/label_config.py`'s `load_labels_config` reads
this file directly; no other wiring needed for the labels themselves to
exist and be usable by `update_workflow_label()`.

## DATA

N/A (static config).

## Test-first steps

1. In `tests/cli/commands/test_define_labels.py`, change the asserted count
   from `41` to `45` (one line, around `len(labels_config["workflow_labels"]) == 41`).
2. In `tests/cli/commands/test_define_labels_label_changes.py`, change the
   asserted created-count from `40` to `44` at all three occurrences (lines
   308, 311, and 366): `len(result["created"]) == 40` (two test methods) and
   `mock_labels_manager.create_label.call_count == 40` (one test method).
   Update the trailing comment on line 308 too:
   `# 44 new labels (45 total - 1 existing)`.
3. Run these two test files — confirm they now fail against the current
   41-label file (red).
4. Edit `labels.json` to add the 4 entries above.
5. Re-run the two test files — confirm green.

## Checks

Run `mcp__mcp-tools-py__run_pytest_check` (fast unit markers), `run_pylint_check`,
`run_mypy_check`. All must pass. Then `run_format_code`, then commit.

## Commit

One commit: `feat(labels): add status-81..84 CI-health labels`.

## LLM Prompt

> Implement Step 1 of the plan in `pr_info/steps/summary.md`. Read that
> summary first for context, then follow `pr_info/steps/step_1.md` exactly:
> update the two label-count test assertions first (red), then add the 4
> new labels (`status-81:failing-ci`, `status-82:fixing-ci`,
> `status-83:ci-fix-failed`, `status-84:pr-ci-failed`) to
> `src/mcp_coder/config/labels.json` exactly as specified (green). If the
> precondition at the top of step_1.md does not hold, write one line to
> `pr_info/.blocked.txt` and stop. Run pytest/pylint/mypy, format, and
> produce exactly one commit.
