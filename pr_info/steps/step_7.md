# Step 7 — `verify` checks every binding (Scope 4)

## LLM prompt

> Read `pr_info/steps/summary.md` (section "`verify` toolkit rows — the rules")
> and this file (`pr_info/steps/step_7.md`). Implement Step 7 only: move
> `_toolkit_rows` into `cli/commands/verify_toolkit_rows.py` as `toolkit_rows`,
> call the toolkit's `verify()` once per requested, declared action, add the
> global-item, per-action and depth rows, delete the Formatter row and
> `_uses_mcp_tools_py`, and stop hiding the `formatter` item. Tests first
> (new file), then code; update the existing fixtures to the new patch target.
> Run format, pylint, mypy, lint-imports, tach and the fast pytest set. One commit.

## WHERE

- `src/mcp_coder/utils/toolkit_runner.py` — rename `_resolve_depth` → `resolve_depth`
  (use `rename_symbol`; internal callers follow)
- `src/mcp_coder/cli/commands/verify_toolkit_rows.py` — add `toolkit_rows`,
  `_requests`, `_formatting_enabled` (moved), `_VERIFY_STATUS_SYMBOL` (moved)
- `src/mcp_coder/cli/commands/verify_sections.py` — delete `_toolkit_rows`,
  `_formatter_row`, `_uses_mcp_tools_py`, `_formatting_enabled`,
  `_VERIFY_STATUS_SYMBOL`, and the imports of `resolve_steps`, `DEFAULT_TOOLKIT`,
  `load_toolkit`, `load_toolkit_config`, `verify_toolkit`; both branches of
  `_print_project_section` call `toolkit_rows(...)` (indent 2 without
  pyproject.toml, 4 with)
- Tests:
  - **new** `tests/cli/commands/test_verify_toolkit_rows.py`
  - `tests/conftest.py::_resolvable_formatter` — add
    `patch("mcp_coder.cli.commands.verify_toolkit_rows.verify_toolkit", lambda _l, _p, _a: [])`
  - `tests/cli/commands/conftest.py::toolkit_with_ruff` — patch target → `verify_toolkit_rows.verify_toolkit`
  - `tests/cli/commands/test_verify_project_section.py` — `_VERIFY_TOOLKIT` → new
    target; delete `TestFormatterRow`, `TestUsesMcpToolsPy`,
    `test_false_is_disabled_formatter_still_evaluated` and every assertion on
    the `Formatter` row or the steps string; `test_formatter_item_skipped` →
    formatter item is shown; `test_verify_raising_is_error` → error row in the
    `format` group (Toolkit row stays `[OK]`); `_toolkit_rows` import →
    `toolkit_rows`; item indents become indent + 4 under an action header;
    `_COMMAND_TOML` / `command_project` declare the default-binding depths
    (`check` quick/standard, `test` quick/standard/unattended) or set the
    bindings so the existing command tests keep passing

## WHAT

```python
def toolkit_rows(project_dir: Path, symbols: dict[str, str], out: SectionBuilder, *, indent: int = 4) -> bool:
    """Toolkit row, global items, then one group per requested action. False on any error row."""

def _requests(bindings: dict[str, tuple[str, ...]], formatting: bool) -> dict[tuple[str, str], list[str]]:
    """(action, depth) → binding entries requesting it, in first-seen order; commit only if formatting."""
```

## HOW

- `verify_toolkit_rows.py` imports `load_toolkit`, `resolve_depth`,
  `verify_toolkit` by name from `...utils.toolkit_runner`, and `get_format_code`
  from `...utils.pyproject_config`. The single patch target for tests is
  `mcp_coder.cli.commands.verify_toolkit_rows.verify_toolkit`.
- Action header: a plain line `" " * (indent + 2) + action` via `out.add(str)`
  (like the `"  [Python]"` line). Global items at `indent + 2`, action items and
  depth rows at `indent + 4`.
- Item key for "same item": `(item.name, item.status, item.message)`.

## ALGORITHM

```
loaded = load_toolkit(...) — ValueError → [ERR] Toolkit row, return False; else [OK] Toolkit row
requests = _requests(loaded.config.bindings, _formatting_enabled(project_dir))
actions = unique actions of requests (first-seen); declared = [a for a in actions if a in loaded.info.actions]
returned, raised = {}, {}  ;  for a in declared: try returned[a] = verify_toolkit(...) except ValueError as e: raised[a] = str(e)
multi = len(returned) >= 2
shared = intersection of item keys over returned.values() if multi else set()
rows: shared items once (own severity); per action: header, raised row (error if format else warning),
      non-shared items (error → warning if multi and action != "format"), depth rows; ok = no [ERR] row added
```

Depth row for `(action, depth)` with `entries`:

```
declared_depths = loaded.info.actions.get(action)
if declared_depths is None: [ERR] f"{action}@{depth}" "action not declared by toolkit '<name>' (requested by ...)"
else: resolved = resolve_depth(declared_depths, depth)
      resolved == depth → no row; resolved → [WARN] "not declared; runs <resolved> (requested by ...)"; None → [ERR] "not declared (requested by ...)"
```

## DATA

- `_requests` → e.g. `{("check","quick"): ["implement_task"], ("check","standard"): ["implement_final","rebase","rebase_automated"], ...}`
- `toolkit_rows` → `bool`.

## Tests (write first, fake toolkit via `_toolkit_class` patch + `verify_toolkit` patched per action)

- one row per distinct request, naming every requesting binding (default
  bindings: `check@standard` lists `implement_final, rebase, rebase_automated`)
- undeclared action → `[ERR]`, `verify()` not called for it
- undeclared `full` with `standard` declared → `[WARN]` "runs standard"; undeclared
  `unattended` → `[ERR]`
- two actions returning: a shared `environment` error shown once, `[ERR]`, False;
  a check-only `error` item → `[WARN]`, True; a `format` `error` item → `[ERR]`, False
- one action returning (e.g. only `check` requested): its `error` item stays `[ERR]`
- `verify()` raising for `check` → `[WARN]` row, action excluded from global
  items; raising for `format` → `[ERR]`
- `format_code = false` → `format` neither verified nor depth-checked
- `formatter` item is shown
- Done-when: a `command` project declaring all requested depths passes
  (`toolkit_rows` True) with mcp-tools-py's entry point absent
