# Step 3: Switch the TASK_TRACKER.md template write to `write_lf_text`

See `pr_info/steps/summary.md` for the full design rationale. Depends on
Step 1 (`write_lf_text` must already exist). Independent of Steps 2, 4, 5.

## Precondition

`src/mcp_coder/workflows/create_plan/prerequisites.py` must still contain,
inside `create_pr_info_structure`, exactly this line:

```python
        task_tracker_path.write_text(TASK_TRACKER_TEMPLATE, encoding="utf-8")
```

If this line is not found verbatim, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- Modify `src/mcp_coder/workflows/create_plan/prerequisites.py`
- Modify `tests/workflows/create_plan/test_prerequisites.py`

## WHAT

No new functions. `create_pr_info_structure`'s signature and return value
(`-> bool`) are unchanged — only its `TASK_TRACKER.md` write call changes.

## HOW

- Add `from mcp_coder.utils.text_io import write_lf_text` to the imports in
  `prerequisites.py`.
- Replace the line identified in Precondition with:

```python
        write_lf_text(task_tracker_path, TASK_TRACKER_TEMPLATE)
```

## ALGORITHM

Not applicable — one-line call substitution.

## DATA

No change to `create_pr_info_structure`'s inputs, outputs, or side effects —
the file on disk now has LF-only bytes instead of possibly CRLF (on
Windows).

## Tests

Add to `TestCreatePrInfoStructure` in
`tests/workflows/create_plan/test_prerequisites.py`:

```python
    def test_task_tracker_has_no_crlf_bytes(self, tmp_path: Path) -> None:
        create_pr_info_structure(tmp_path)
        task_tracker_path = tmp_path / "pr_info" / "TASK_TRACKER.md"
        assert b"\r" not in task_tracker_path.read_bytes()
```

Write this test first, confirm it fails on Windows / passes trivially on
Linux against the current code, then apply the implementation change above.
All existing tests in this file must stay green unmodified.

## Checks

Run, in order, and fix anything that fails before committing:

- `mcp__mcp-tools-py__run_pytest_check`, scoped to
  `tests/workflows/create_plan/test_prerequisites.py`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_tach_check`
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-tools-py__run_format_code`

## Commit

One commit: `fix(create_plan): write TASK_TRACKER.md with LF-only line endings`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_3.md`). Implement Step 3 exactly as specified: add
> the test to `tests/workflows/create_plan/test_prerequisites.py` first,
> confirm it fails, then make the one-line change in
> `src/mcp_coder/workflows/create_plan/prerequisites.py` to make it pass. If
> the precondition in this file does not hold, write one line to
> `pr_info/.blocked.txt` and stop — do not improvise a different fix. Run
> the checks listed under "Checks" and fix any failures. Format code, then
> make exactly one commit for this step.
