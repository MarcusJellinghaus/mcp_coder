# Step 8 — `mcp-coder verify` gating (Scope 8a)

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 8a and the
"Done when" item for `mcp-coder verify`. Depends on Steps 1–3.

## LLM prompt

> Implement Step 8 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_8.md`: in `verify_sections.py`, call the toolkit's
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
def _toolkit_rows(project_dir: Path, symbols: dict[str, str], *, indent: int = 4) -> bool  # unchanged signature
def _uses_mcp_tools_py(project_dir: Path) -> bool  # new
```

## ALGORITHM

`_toolkit_rows` (return type stays `bool`):
```
loaded = load_toolkit(project_dir)            # error -> Toolkit [ERR] row, return False, as today
print Toolkit row (loaded.name)
if not (get_format_code(project_dir).enabled and loaded.config.bindings["commit"]):
    return True                               # no verify("format"), no item rows
items = verify_toolkit(loaded, project_dir, "format"); print item rows and return as today
```
`_uses_mcp_tools_py`: `load_toolkit_config(project_dir).toolkit == DEFAULT_TOOLKIT`;
`ValueError` → `False` (the Toolkit row already reports the config error).

`_print_project_section`: in both branches, call `_formatter_row(...)` only
when `_uses_mcp_tools_py(project_dir)`; otherwise it contributes `True`.
- `get_format_code` raising `ValueError` inside `_toolkit_rows`: treat as
  enabled (in the pyproject branch `_format_code_row` already prints the
  `[ERR]`; without `pyproject.toml` it defaults to enabled anyway).
- `DEFAULT_TOOLKIT` from `toolkit_runner` names `"mcp-tools-py"`; compare with it.

## DATA

Unchanged output format; rows are omitted, never renamed.

## Tests

- `command` project with only `mcp-coder.toml` (`_toolkit_class` patched to
  `CommandToolkit`): `_print_project_section` returns `True`; no "Formatter"
  row, no `[ERR]` from mcp-tools-py; Toolkit row shows `command`.
- Same project with `bindings.commit = []`: `_toolkit_rows` returns `True`,
  `verify_toolkit` not called (mock).
- `format_code = false` in `pyproject.toml`: `_toolkit_rows` returns `True`,
  `verify_toolkit` not called.
- `_uses_mcp_tools_py`: `True` with no config, `False` for `toolkit = "command"`,
  `False` on an invalid config.
- `mcp-tools-py` project: Formatter row and toolkit items still shown (existing tests keep passing).
- Broken `command` config (unknown key) with formatting on: the global error
  item is printed as `[ERR]`; `_toolkit_rows` and the section return `False`.
