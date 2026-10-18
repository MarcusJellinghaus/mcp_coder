# Step 2: Switch the review round-log append to `write_lf_text`

See `pr_info/steps/summary.md` for the full design rationale. Depends on
Step 1 (`write_lf_text` must already exist).

## Precondition

`src/mcp_coder/workflows/review/review_log.py` must still contain, inside
`write_round_log`, exactly this block:

```python
    with path.open("a", encoding="utf-8") as handle:
        handle.write("".join(parts))
```

If this pattern is not found verbatim (the function has since changed),
write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- Modify `src/mcp_coder/workflows/review/review_log.py`
- Modify `tests/workflows/review/test_review_log.py`

## WHAT

No new functions. `write_round_log`'s signature and return value
(`-> Path`) are unchanged — only its final write call changes.

## HOW

- Add `from mcp_coder.utils.text_io import write_lf_text` to the imports in
  `review_log.py`.
- Replace the block identified in Precondition with:

```python
    write_lf_text(path, "".join(parts), append=True)
```

## ALGORITHM

Not applicable — this is a one-line call substitution, no new logic.

## DATA

No change to `write_round_log`'s inputs, outputs, or side effects — the file
on disk now has LF-only bytes instead of possibly CRLF (on Windows).

## Tests

Add to `TestWriteRoundLog` in `tests/workflows/review/test_review_log.py`:

```python
    def test_round_log_bytes_have_no_crlf(self, tmp_path: Path) -> None:
        path = write_round_log(
            tmp_path,
            REVIEW_IMPLEMENTATION,
            run_number=1,
            round_number=1,
            findings="f",
            decisions="d",
            changes="c",
        )
        assert b"\r" not in path.read_bytes()
```

Write this test first (it fails on Windows against the current code before
the implementation change, and is a no-op assertion on Linux — that is
expected and matches the issue's documented test strategy). Then apply the
implementation change above so the test passes everywhere. All existing
tests in this file must stay green unmodified.

## Checks

Run, in order, and fix anything that fails before committing:

- `mcp__mcp-tools-py__run_pytest_check`, scoped to
  `tests/workflows/review/test_review_log.py`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_tach_check`
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-tools-py__run_format_code`

## Commit

One commit: `fix(review): write round log with LF-only line endings`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_2.md`). Implement Step 2 exactly as specified: add
> the test to `tests/workflows/review/test_review_log.py` first, confirm it
> fails, then make the one-line change in
> `src/mcp_coder/workflows/review/review_log.py` to make it pass. If the
> precondition in this file does not hold, write one line to
> `pr_info/.blocked.txt` and stop — do not improvise a different fix. Run
> the checks listed under "Checks" and fix any failures. Format code, then
> make exactly one commit for this step.
