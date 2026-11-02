# Step 8 — Label config: `status-72` and `status-74`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_8.md` only.
> Write the tests first, then the change. Run pylint, pytest (fast unit set,
> `-n auto`), mypy and lint-imports until they pass, run `run_format_code`, and
> make exactly one commit.

## WHERE

- `src/mcp_coder/config/labels.json`
- Tests: `tests/cli/commands/test_define_labels_config.py`
  (`test_expected_timeout_values`) or `tests/config/test_label_config.py`

## WHAT / HOW

- `status-72:fixing-merge-conflict`:
  - `stale_timeout_minutes`: 15 → 60
  - `description`: `"Rebase in progress to resolve merge conflict (auto/in-progress)"`
    (drop "Mechanical").
- `status-74:pr-merge-conflict` → `vscodeclaude.commands`: `["/rebase", "/check_branch_status"]`.
- `status-73` unchanged.

## ALGORITHM

None (config only).

## DATA

JSON only.

## Tests

- `fixing_merge_conflict` has `stale_timeout_minutes == 60` and no "Mechanical" in
  its description (add it to `expected_timeouts`).
- `pr_merge_conflict` commands == `["/rebase", "/check_branch_status"]`.
- `merge_conflict_failed` commands still `["/check_branch_status"]`.
