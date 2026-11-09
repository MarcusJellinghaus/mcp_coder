# Step 7 — `mcp-coder verify` gating (Scope 8a)

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 8a and the
"Done when" item for `mcp-coder verify`. Depends on Steps 1–3.

## LLM prompt

> Implement Step 7 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_7.md`: in `verify_sections.py`, call the toolkit's
> `verify("format")` only when formatting is on and the commit binding is
> non-empty, and show the mcp-tools-py Formatter row only for the
> `mcp-tools-py` toolkit (TDD — tests first). Run the code-quality checks from
> CLAUDE.md and make exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py` — `_toolkit_rows`,
  `_print_project_section`.
- Tests: the existing test module for `verify_sections` (find with
  `search_files` for `_toolkit_rows` under `tests/`).

## WHAT

```python
def _toolkit_rows(project_dir: Path, symbols: dict[str, str], *, indent: int = 4) -> tuple[bool, str | None]
    # returns (ok, loaded toolkit name or None)
```
(Or keep the `bool` return and load the toolkit once in `_print_project_section`;
pick whichever keeps the diff smaller.)

## ALGORITHM

```
loaded = load_toolkit(project_dir)            # error -> Toolkit [ERR] row, as today
print Toolkit row (loaded.name)
if get_format_code(project_dir).enabled and loaded.config.bindings["commit"]:
    items = verify_toolkit(loaded, project_dir, "format"); print item rows as today
_formatter_row(...) only if loaded.name == "mcp-tools-py"   # in both branches of _print_project_section
```
- `get_format_code` raising `ValueError`: treat like today's `_format_code_row`
  failure (row already printed in the pyproject branch); in the no-pyproject
  branch it defaults to enabled.
- `DEFAULT_TOOLKIT` from `toolkit_runner` names `"mcp-tools-py"`; compare with it.

## DATA

Unchanged output format; rows are omitted, never renamed.

## Tests

- `command` project with only `mcp-coder.toml` (`_toolkit_class` patched to
  `CommandToolkit`): no "Formatter" row, no `[ERR]` from mcp-tools-py; Toolkit row shows `command`.
- Same project with `bindings.commit = []`: `verify_toolkit` not called (mock).
- `format_code = false` in `pyproject.toml`: `verify_toolkit` not called.
- `mcp-tools-py` project: Formatter row and toolkit items still shown (existing tests keep passing).
- Broken `command` config (unknown key) with formatting on: the global error
  item is printed as `[ERR]` and the section returns `False`.
