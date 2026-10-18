# Step 4: Switch the label-workflow YAML writes to `write_lf_text`

See `pr_info/steps/summary.md` for the full design rationale. Depends on
Step 1 (`write_lf_text` must already exist). Independent of Steps 2, 3, 5.

## Precondition

`src/mcp_coder/cli/commands/define_labels_actions.py` must still contain,
inside `write_github_actions`, exactly this loop body:

```python
    for path, content in files_to_write.items():
        if path.exists():
            logger.warning("Overwriting: %s", path)
        path.write_text(content, encoding="utf-8")
```

If this block is not found verbatim, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- Modify `src/mcp_coder/cli/commands/define_labels_actions.py`
- Modify `tests/cli/commands/test_define_labels_actions.py`

## WHAT

No new functions. `write_github_actions`'s signature and return value
(`-> list[str]`) are unchanged — only the final write call inside the loop
changes.

## HOW

- Add `from mcp_coder.utils.text_io import write_lf_text` to the imports in
  `define_labels_actions.py`.
- Replace the last line of the loop body identified in Precondition with:

```python
        write_lf_text(path, content)
```

(The `if path.exists(): logger.warning(...)` line is unchanged.)

## ALGORITHM

Not applicable — one-line call substitution inside the existing loop.

## DATA

No change to `write_github_actions`'s inputs, outputs, or side effects — the
two files on disk (`label-new-issues.yml`, `approve-command.yml`) now have
LF-only bytes instead of possibly CRLF (on Windows).

## Tests

Add to `TestWriteGithubActions` in
`tests/cli/commands/test_define_labels_actions.py`:

```python
    def test_written_files_have_no_crlf_bytes(self, tmp_path: Path) -> None:
        config = self._make_config()
        write_github_actions(tmp_path, config)
        workflows_dir = tmp_path / ".github" / "workflows"
        for name in ("label-new-issues.yml", "approve-command.yml"):
            assert b"\r" not in (workflows_dir / name).read_bytes()
```

Write this test first, confirm it fails on Windows / passes trivially on
Linux against the current code, then apply the implementation change above.
All existing tests in this file must stay green unmodified.

## Checks

Run, in order, and fix anything that fails before committing:

- `mcp__mcp-tools-py__run_pytest_check`, scoped to
  `tests/cli/commands/test_define_labels_actions.py`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_tach_check`
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-tools-py__run_format_code`

## Commit

One commit: `fix(cli): write label workflow YAML files with LF-only line endings`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_4.md`). Implement Step 4 exactly as specified: add
> the test to `tests/cli/commands/test_define_labels_actions.py` first,
> confirm it fails, then make the one-line change in
> `src/mcp_coder/cli/commands/define_labels_actions.py` to make it pass. If
> the precondition in this file does not hold, write one line to
> `pr_info/.blocked.txt` and stop — do not improvise a different fix. Run
> the checks listed under "Checks" and fix any failures. Format code, then
> make exactly one commit for this step.
