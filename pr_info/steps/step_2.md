# Step 2 — E741: rename `l` → `line` across 8 test files

See `pr_info/steps/summary.md` for the overall goal and rationale.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E741"]` and
`extra_args=["--preview"]`. Confirm it reports `E741` at exactly these 35
locations (file:line), and no others besides the ones handled by step 1 and
step 3:

- `tests/cli/commands/test_prompt_streaming.py`: 149, 181, 210, 279
- `tests/cli/commands/test_set_status.py`: 152, 153, 159, 160
- `tests/cli/commands/test_verify.py`: 395, 396, 420, 421, 700, 728, 729
- `tests/cli/commands/test_verify_format_mcp_section.py`: 57, 132, 186, 254, 316
- `tests/cli/commands/test_verify_format_section_basic.py`: 106, 112, 150, 177, 201, 218
- `tests/cli/commands/test_verify_mcp_orchestration.py`: 632, 633
- `tests/cli/commands/test_verify_sections_config.py`: 122, 123
- `tests/cli/commands/test_verify_sections_orchestration.py`: 85, 100, 111, 137
- `tests/utils/test_user_config_create_default.py`: 187

If the locations differ, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

The 9 files listed above. Every flagged site is a comprehension or
generator expression that filters or extracts a line of **text output**
(e.g. CLI/report output split into lines), of the form:

```python
next(l for l in lines if ...)
[l for l in lines if ...]
```

## WHAT

No function signatures change. In each flagged site, rename the loop
variable `l` to `line` — it holds one line of output text, so `line` states
what it is. This is purely mechanical: the flagged `l` is a loop/generator
variable, never a dict or domain object.

## HOW

Use `mcp__mcp-workspace__edit_file` with `replace_all=True` per file,
replacing the exact substrings `l for l in` → `line for line in`, plus any
remaining bare `l` token used only as the yielded/returned value or in an
`l.something` / `l[...]` / `in l` expression tied to that same loop (e.g.
`l.lstrip()`, `l.strip()`, `l["..."]`, `"..." in l`). Confirm with
`mcp__mcp-tools-py__find_references`-style reading (just look at the
surrounding lines from the precondition check) that no other `l` exists in
that file outside these comprehensions before using `replace_all` — if a
file has an unrelated `l`, replace the comprehension's occurrences
individually with non-`replace_all` edits instead.

## ALGORITHM

Same pattern repeated per site:

```
line = next(line for line in lines if <condition on line>)
# or
result_lines = [line for line in lines if <condition on line>]
```

## DATA

No change to return values or data structures — results are still the same
line string(s)/list(s) as before.

## Test-first note

Pure local-variable renames with no behavioral change. No new tests;
verification is the existing test suite passing unchanged.

## Steps

1. For each of the 9 files, rename `l` → `line` at the flagged
   comprehension/generator sites (and their associated `l.`/`l[`/`in l`
   usages within the same expression).
2. Run `mcp__mcp-tools-py__run_pytest_check` with
   `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`.
3. Run `mcp__mcp-tools-py__run_pylint_check` and `mcp__mcp-tools-py__run_mypy_check`.
4. Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E741"]`,
   `extra_args=["--preview"]` — must report 0 findings in these 9 files.
5. Run `mcp__mcp-tools-py__run_format_code`.
6. Commit: `fix(lint): rename ambiguous l to line in test output comprehensions`.

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_2.md`: rename the ambiguous loop variable `l` to
> `line` at the 35 listed locations across the 9 test files (all are
> output-line comprehensions/generators). Follow the precondition check
> first — if it fails, write one line to `pr_info/.blocked.txt` and stop.
> Otherwise make the renames, run the checks listed in the step, format the
> code, and produce exactly one commit with the given message.
