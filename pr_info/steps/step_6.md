# Step 6: Switch the `.vscode/tasks.json` write to `write_lf_text`

See `pr_info/steps/summary.md` for the full design rationale. Depends on
Step 1 (`write_lf_text` must already exist). Independent of Steps 2-5, 7, 8.

## Precondition

`src/mcp_coder/workflows/vscodeclaude/workspace.py` must still contain,
inside `create_vscode_task`, exactly this line:

```python
    tasks_file.write_text(content, encoding="utf-8")
```

If this line is not found verbatim, write one line to
`pr_info/.blocked.txt` and stop.

Do **not** touch the `.vscodeclaude_start.bat` / `.sh` launcher write in
`create_startup_script` (`script_path.write_text(...)`): `.gitattributes`
sets `*.bat text eol=crlf`, so forcing LF there would be wrong.

## WHERE

- Modify `src/mcp_coder/workflows/vscodeclaude/workspace.py`
- Modify `tests/workflows/vscodeclaude/test_workspace.py`

## WHAT

No new functions. `create_vscode_task`'s signature and return value
(`-> None`) are unchanged — only its final write call changes.

## HOW

- Add the import for `write_lf_text` following the import style the file
  already uses for `mcp_coder.utils` (or, if it has none, the package-relative
  style used by its sibling modules: `from ...utils.text_io import
  write_lf_text`). Keep imports isort-ordered.
- Replace the line identified in Precondition with:

```python
    write_lf_text(tasks_file, content)
```

## ALGORITHM

Not applicable — one-line call substitution.

## DATA

No change to `create_vscode_task`'s inputs, outputs, or side effects — the
file on disk now has LF-only bytes instead of possibly CRLF (on Windows).

## Tests

Add to the class containing `test_create_vscode_task` in
`tests/workflows/vscodeclaude/test_workspace.py`:

```python
    def test_create_vscode_task_writes_no_crlf_bytes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """tasks.json has LF-only bytes even if the template contains CRLF."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.templates.TASKS_JSON_TEMPLATE",
            '{{\r\n  "command": "{script_path}"\r\n}}\r\n',
        )
        script_path = tmp_path / ".vscodeclaude_start.bat"
        script_path.touch()

        create_vscode_task(tmp_path, script_path)

        content = (tmp_path / ".vscode" / "tasks.json").read_bytes()
        assert b"\r" not in content
```

`create_vscode_task` imports `TASKS_JSON_TEMPLATE` from `.templates` at call
time, so patching the attribute on the `templates` module takes effect. The
replacement must stay a valid `str.format` template (doubled braces, one
`{script_path}` field). Injecting `\r\n` makes this test fail on every OS
against the current `write_text` code, not just Windows.

Write this test first, confirm it fails, then apply the implementation
change. Add `import pytest` to the test module only if it is not already
imported. All existing tests in this file must stay green unmodified.

## Checks

Run, in order, and fix anything that fails before committing:

- `mcp__mcp-tools-py__run_pytest_check`, scoped to
  `tests/workflows/vscodeclaude/test_workspace.py`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_tach_check`
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-tools-py__run_format_code`

## Commit

One commit: `fix(vscodeclaude): write .vscode/tasks.json with LF-only line endings`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_6.md`). Implement Step 6 exactly as specified: add
> the test to `tests/workflows/vscodeclaude/test_workspace.py` first,
> confirm it fails, then make the one-line change in
> `src/mcp_coder/workflows/vscodeclaude/workspace.py` to make it pass. Do
> not touch the launcher script write. If the precondition in this file
> does not hold, write one line to `pr_info/.blocked.txt` and stop — do not
> improvise a different fix. Run the checks listed under "Checks" and fix
> any failures. Format code, then make exactly one commit for this step.
