# Step 8: Move `_read_problem_description` into a new helpers module

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_8.md`. This is a refactor with no behaviour change, so the existing tests are the safety net. Run the checks listed in the summary. Make exactly one commit's worth of change.

## WHERE

- `src/mcp_coder/workflow_steps/ci_fix_helpers.py` (new)
- `src/mcp_coder/workflow_steps/ci.py`

## WHAT

Move `_read_problem_description(temp_file: Path, fallback_response: str) -> str` unchanged. The new module gets a docstring and its own `logger`.

## HOW

- Use `mcp__mcp-tools-py__move_symbol`, or move it by hand.
- `ci.py` calls the function, so it must import it from `.ci_fix_helpers`. Existing tests importing it from `ci` keep working. If the tool rewrites those imports to the new module, that is fine too.

## ALGORITHM

None. The function body is unchanged.

## DATA

Unchanged.

## TESTS

No new tests. `TestReadProblemDescription` in `tests/workflow_steps/test_ci_check_and_fix.py` must still pass.

After the move, run `mcp__mcp-workspace__check_file_size` with `max_lines=750` to confirm `ci.py` and the other touched files are under the limit.
