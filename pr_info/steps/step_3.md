# Step 3 — E741: rename inner `l` → `entry` in `test_label_config.py`

See `pr_info/steps/summary.md` for the overall goal and rationale.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E741"]` and
`extra_args=["--preview"]`. Confirm it reports `E741` at exactly these 6
locations in `tests/config/test_label_config.py`: lines 182, 195, 250, 273,
284, 296. If the locations differ, write one line to `pr_info/.blocked.txt`
and stop.

## WHERE

`tests/config/test_label_config.py`, 6 sites, each of the form:

```python
label = next(
    l for l in config["workflow_labels"] if l["internal_id"] == internal_id
)
```

(lines 182, 195, 273, 284, 296 are bare `next(l for l in ...)`; line 250 is
`next((l for l in ...), None)`; line 296's site spans a multi-line
generator with the filter on its own line — same shape.)

## WHAT

No function signatures change. The outer result is already bound to
`label`, so renaming the inner loop variable to `label` as well would read
as self-referential (`label = next(label for label in ... if label[...] ==
...)`). Rename the inner loop variable to `entry` instead — it holds one
raw `workflow_labels` entry being tested before `label` is bound to the
match.

## HOW

Use `mcp__mcp-workspace__edit_file` (not `replace_all`, since `label` also
appears as a token in this file and a blind replace could touch the wrong
occurrences) for each of the 6 sites individually, changing `l for l in` →
`entry for entry in` and the matching `l[...]` / `l.get(...)` inside that
same comprehension to `entry[...]` / `entry.get(...)`.

## ALGORITHM

```
label = next(
    entry for entry in config["workflow_labels"]
    if entry["internal_id"] == internal_id
)
```

## DATA

No change to return values or data structures — `label` is still the
matching `workflow_labels` dict (or `None` where the site uses the
`next(..., None)` form).

## Test-first note

Pure local-variable rename with no behavioral change. No new tests;
verification is the existing test suite passing unchanged.

## Steps

1. At lines 182, 195, 250, 273, 284, 296, rename the inner loop variable `l`
   to `entry` in each generator expression.
2. Run `mcp__mcp-tools-py__run_pytest_check` with
   `extra_args=["-n", "auto", "tests/config/test_label_config.py"]`, then
   the full unit-test selection:
   `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`.
3. Run `mcp__mcp-tools-py__run_pylint_check` and `mcp__mcp-tools-py__run_mypy_check`.
4. Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E741"]`,
   `extra_args=["--preview"]` — must report 0 findings in this file.
5. Run `mcp__mcp-tools-py__run_format_code`.
6. Commit: `fix(lint): rename ambiguous l to entry in test_label_config.py`.

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_3.md`: rename the inner ambiguous loop variable `l` to
> `entry` at the 6 listed locations in `tests/config/test_label_config.py`
> (the outer result stays bound to `label`). Follow the precondition check
> first — if it fails, write one line to `pr_info/.blocked.txt` and stop.
> Otherwise make the renames, run the checks listed in the step, format the
> code, and produce exactly one commit with the given message.
