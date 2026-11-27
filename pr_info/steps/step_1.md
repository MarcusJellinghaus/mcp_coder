# Step 1 — create-plan logs steps 4, 5 and 6 when each prompt starts

Read `pr_info/steps/summary.md` first.

## WHERE

- `src/mcp_coder/workflows/create_plan/core.py`
  - `run_planning_prompts` (the "Executing prompt N" lines, about lines 230, 302
    and 348)
  - `run_create_plan_workflow` (the "Step 4/7", "Step 5/7" and "Step 6/7" block,
    about lines 626–635)
- `tests/workflows/create_plan/test_prompt_execution.py` (class
  `TestRunPlanningPrompts`)

## WHAT

No signature changes. `run_planning_prompts(project_dir, issue_data, provider,
mcp_config=None, settings_file=None) -> tuple[bool, WorkflowFailure | None]`
stays as it is.

## HOW

- In `run_planning_prompts`, replace:
  - `logger.info("Executing prompt 1: Initial Analysis...")` with
    `logger.info(f"Step 4/7: Running initial analysis for issue #{issue_data['number']} '{issue_data['title']}'...")`.
    Keep the f-string style used nearby.
  - `logger.info("Executing prompt 2: Simplification Review...")` with
    `logger.info("Step 5/7: Running simplification review...")`.
  - `logger.info("Executing prompt 3: Implementation Plan Creation...")` with
    `logger.info("Step 6/7: Generating implementation plan...")`.
- In `run_create_plan_workflow`, delete the three step `logger.info` calls and
  their `# Step 4/5/6` comments directly before `run_planning_prompts(...)`. Add a
  one-line comment `# Steps 4-6: run_planning_prompts logs each one as it starts`.
- The file must not grow; it is at 742 of 750 lines. Check with
  `check_file_size`.

## ALGORITHM (test)

```
calls = []                                   # records seen at each prompt_llm call
def fake_llm(*a, **k):
    calls.append(len(caplog.records)); return responses[len(calls) - 1]
run_planning_prompts(...) under caplog.at_level(INFO)
msgs = [r.getMessage() for r in caplog.records]
i4, i5, i6 = index of the first message starting "Step 4/7", "Step 5/7", "Step 6/7"
assert i4 < calls[0] <= i5 < calls[1] <= i6 < calls[2]
```

## DATA

Log messages only. "Step 4/7" includes `#<number>` and the issue title.

## Tests (write first)

Add `test_step_lines_logged_when_each_prompt_starts` to `TestRunPlanningPrompts`:

- Patch `get_prompt`, `prompt_llm` and `store_session` as
  `test_run_planning_prompts_success` does. Each response carries a `session_id`.
- Assert the ordering above, which proves "Step 5/7" is logged after prompt 1's
  call returns and "Step 6/7" after prompt 2's.
- Assert `"Test Issue"` (the title) is in the "Step 4/7" message.
- Assert that no message starts with `"Executing prompt"`.

Run the existing tests in `tests/workflows/create_plan/`. If any asserts the old
"Executing prompt" or step lines, update it to the new location.

## LLM prompt

> Implement Step 1 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_1.md`.
>
> 1. Write the new ordering test in
>    `tests/workflows/create_plan/test_prompt_execution.py` and see it fail.
> 2. Move the Step 4/5/6 log lines from `run_create_plan_workflow` into
>    `run_planning_prompts`, replacing the "Executing prompt N" lines. Keep
>    `core.py` at or below its current line count.
> 3. Run `run_format_code`, then pylint, mypy and pytest (fast unit set with
>    `-n auto`), and fix any findings.
> 4. Commit as one commit: `fix(create-plan): log steps 4-6 when each prompt starts`.
