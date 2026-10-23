# Step 4 — `labels.json`: `status-09:pr-creating` stale timeout 30 min

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` exactly.
> Update the test first, then the config. Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass.
> Format the code and make exactly one commit for this step.

## WHERE
- `src/mcp_coder/config/labels.json` — entry `"internal_id": "pr_creating"`
- `tests/cli/commands/test_define_labels_config.py` (~line 68, `"pr_creating": 15`)

## WHAT
`"stale_timeout_minutes": 15` → `30` for `pr_creating` only.

## HOW
Rationale (for the commit message, not code): summary LLM (~5 min) + CI poll cap (12.5 min) + two mergeable polls
(~25 s each) + refresh LLM (~5 min) ≈ 23.5 min.

## Tests
- Change the expected value for `pr_creating` in `test_define_labels_config.py` to 30.
- Leave the `stale_timeout_minutes: 15` fixtures in `test_define_labels_execute.py` / `test_define_labels_validate.py`
  alone — they are synthetic fixtures, not the shipped config. Verify that by reading them before deciding.

## DATA
None.
