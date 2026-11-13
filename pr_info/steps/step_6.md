# Step 6: `verify` `Setup` row

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_6.md`) only. Steps 1–2 must be done: if `load_setup_config` or `resolve_executable` does not exist, write one line to `pr_info/.blocked.txt` and stop.
Write the tests first, then the implementation. Keep the new logic out of `verify_sections.py` and the new tests out of `test_verify.py` (both near the size limit). Run format, pylint, pytest (unit filter, `-n auto`), mypy, lint-imports and tach; all must pass. One commit.

## WHERE

- Modify `src/mcp_coder/utils/executable.py` — add `venv_python`
- Create `src/mcp_coder/cli/commands/verify_setup.py`
- Modify `src/mcp_coder/cli/commands/verify_sections.py` — call `setup_rows` in both branches of `_print_project_section`, after `_toolkit_rows`
- Create `tests/cli/commands/test_verify_setup.py`
- Update existing assertions in `tests/cli/commands/test_verify_project_section.py` / `test_verify_alignment.py` only if the extra row breaks them

## WHAT

```python
# utils/executable.py
def venv_python(venv_root: Path) -> Path | None:
    """The venv's interpreter (Scripts/python.exe on win32, bin/python elsewhere) if it is a file."""
    # built on mcp_verification.get_bin_dir; exe name decided by sys.platform

# cli/commands/verify_setup.py
def setup_rows(project_dir: Path, symbols: dict[str, str], out: SectionBuilder, *, indent: int = 4) -> bool:
    """Add the Setup row (+ one sub-row per problem). False on any error."""
```

## ALGORITHM

```
try: config = load_setup_config(project_dir)
except ValueError as exc: add Row("Setup", failure, str(exc)); return False
has_venv = venv_python(project_dir / ".venv") is not None; after_python = False; problems = []
for step in config.steps: builtin -> after_python |= builtin == "python"; continue
    if resolve_executable(argv[0], project_dir, path=venv_search_path(project_dir) if after_python else None) is None:
        problems.append(("warning" if after_python and not has_venv else "error", f"{step.label}: {argv[0]!r} not found"))
add Row("Setup", worst symbol, summary); add sub-rows for problems at indent + 2; return no "error" in problems
```

Summary text: `"<n> step(s) from <source>"`, `"default: python built-in"` when `source is None` and steps exist, `"nothing to do"` when no steps.

## HOW

- `Row` / `SectionBuilder` come from `.verify_formatting`, as in `verify_sections.py`; reuse the `_VERIFY_STATUS_SYMBOL`-style mapping (`ok`→`success`, `warning`→`warning`, `error`→`failure`).
- Built-in names are already validated by the loader; no step is executed.
- `indent=2` in the no-`pyproject.toml` branch, default `4` in the Python branch — same as `_toolkit_rows`.

## Tests

- Valid `npm ci` config with `npm` on `PATH` → ok row, returns True (patch `resolve_executable` in the module).
- Broken config → failure row with the loader message, False.
- Unresolvable `argv[0]` before / without the built-in → error, False.
- Unresolvable `argv[0]` after the built-in, no `.venv` interpreter → warning, True; with interpreter → error, False; resolver received the venv `path`.
- No table, no `pyproject.toml` → "nothing to do", True.
- `venv_python`: win32 → `Scripts/python.exe`, linux → `bin/python`, missing → None.

## DATA

`bool` (False when any row is an error).
