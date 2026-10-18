# Step 7: Switch the verify smoke-test probe write to `write_lf_text`

See `pr_info/steps/summary.md` for the full design rationale. Depends on
Step 1 (`write_lf_text` must already exist). Independent of Steps 2-6, 8.

## Precondition

`src/mcp_coder/cli/commands/verify.py` must still contain, inside
`_run_mcp_edit_smoke_test`, exactly this line:

```python
        test_file.write_text("A\n\nC\n", encoding="utf-8")
```

If this line is not found verbatim, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- Modify `src/mcp_coder/cli/commands/verify.py`

No test file is added or modified (see Tests).

## WHAT

No new functions. `_run_mcp_edit_smoke_test`'s signature and return value
(`-> str`) are unchanged — only the probe-file write changes.

## HOW

- Add `from ...utils.text_io import write_lf_text` to the imports in
  `verify.py`, between the existing `from ...utils.mcp_verification import ...`
  and `from ...utils.user_config import ...` lines (isort order).
- Replace the line identified in Precondition with:

```python
        write_lf_text(test_file, "A\n\nC\n")
```

## ALGORITHM

Not applicable — one-line call substitution.

## DATA

No change to inputs, outputs, or side effects. The probe file
(`.mcp_coder_verify.md`) is transient — it is removed in the existing
`finally` block — and its content is a fixed LF-only literal.

## Tests

No new test, per the issue's decision: the content is a fixed literal that
cannot contain `\r`, and the file is removed after use. The existing tests in
`tests/cli/commands/test_verify_mcp_edit_smoke.py` (including
`test_smoke_test_cleans_up_file`) must stay green unmodified; they are the
check that the substitution did not change behaviour.

## Checks

Run, in order, and fix anything that fails before committing:

- `mcp__mcp-tools-py__run_pytest_check`, scoped to
  `tests/cli/commands/test_verify_mcp_edit_smoke.py` and then
  `tests/cli/commands/` (other verify tests import this module)
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_tach_check`
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-tools-py__run_format_code`

## Commit

One commit: `fix(verify): write smoke-test probe file with LF-only line endings`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_7.md`). Implement Step 7 exactly as specified: make
> the one-line change in `src/mcp_coder/cli/commands/verify.py` and add the
> import. No new test is needed; confirm the existing smoke-test tests stay
> green. If the precondition in this file does not hold, write one line to
> `pr_info/.blocked.txt` and stop — do not improvise a different fix. Run
> the checks listed under "Checks" and fix any failures. Format code, then
> make exactly one commit for this step.
