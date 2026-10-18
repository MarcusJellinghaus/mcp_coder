# Step 5: Switch the iCoder schema write to `write_lf_text`

See `pr_info/steps/summary.md` for the full design rationale. Depends on
Step 1 (`write_lf_text` must already exist). Independent of Steps 2, 3, 4.

## Precondition

`src/mcp_coder/icoder/permissions/loader.py` must still contain, inside
`emit_schema`, exactly this line:

```python
        target.write_text(new, encoding="utf-8")
```

If this line is not found verbatim, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- Modify `src/mcp_coder/icoder/permissions/loader.py`
- Modify `tests/icoder/test_permissions_loader_schema.py`

## WHAT

No new functions. `emit_schema`'s signature and return value (`-> bool`)
are unchanged — only its write call changes. The existing `read_text`
comparison (universal newlines) that gates the write is unchanged, so an
already-committed CRLF schema file is not rewritten until its content
changes — this is explicitly out of scope per the issue.

## HOW

- Add `from mcp_coder.utils.text_io import write_lf_text` to the imports in
  `loader.py`. (This module already imports from `mcp_coder.utils` —
  `get_user_app_data_dir` — so the new import follows an existing,
  already-permitted dependency path; no `tach.toml`/`.importlinter` change
  is needed.)
- Replace the line identified in Precondition with:

```python
        write_lf_text(target, new)
```

## ALGORITHM

Not applicable — one-line call substitution.

## DATA

No change to `emit_schema`'s inputs, outputs, or side effects — the file on
disk now has LF-only bytes instead of possibly CRLF (on Windows). The
`\r\n`-normalization case does not apply here (`json.dumps` cannot emit a
raw `\r`), so this step's test is a Windows bytes-regression guard only —
already proven generically by Step 1's helper tests.

## Tests

Add to `tests/icoder/test_permissions_loader_schema.py` (module-level
function, matching the existing style in that file):

```python
def test_emit_schema_writes_no_crlf_bytes(tmp_path: Path) -> None:
    """Written schema file has LF-only bytes (Windows regression guard)."""
    (tmp_path / ".icoder").mkdir()
    assert emit_schema(tmp_path) is True
    target = tmp_path / ".icoder" / "settings.schema.json"
    assert b"\r" not in target.read_bytes()
```

Write this test first, confirm it fails on Windows / passes trivially on
Linux against the current code, then apply the implementation change above.
All existing tests in this file must stay green unmodified.

## Checks

Run, in order, and fix anything that fails before committing:

- `mcp__mcp-tools-py__run_pytest_check`, scoped to
  `tests/icoder/test_permissions_loader_schema.py`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_tach_check`
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-tools-py__run_format_code`

## Commit

One commit: `fix(icoder): write permission schema with LF-only line endings`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_5.md`). Implement Step 5 exactly as specified: add
> the test to `tests/icoder/test_permissions_loader_schema.py` first,
> confirm it fails, then make the one-line change in
> `src/mcp_coder/icoder/permissions/loader.py` to make it pass. If the
> precondition in this file does not hold, write one line to
> `pr_info/.blocked.txt` and stop — do not improvise a different fix. Run
> the checks listed under "Checks" and fix any failures. Format code, then
> make exactly one commit for this step.
