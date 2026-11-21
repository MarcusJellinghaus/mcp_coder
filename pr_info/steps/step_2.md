# Step 2 — Retire `check_type_hints`; `verify` leftover row (Scope 5)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`).
> Implement Step 2 only: remove `check_type_hints` from the implement workflow
> and config reader, add the leftover-key reader and the `verify` leftover row in
> the new module `cli/commands/verify_toolkit_rows.py`. Write the tests first
> (TDD), then the code. Run format, pylint, mypy and the fast pytest set; all
> must pass. One commit.

## WHERE

- `src/mcp_coder/utils/pyproject_config.py` — delete `ImplementConfig`,
  `get_implement_config`; add `get_leftover_check_type_hints`
- `src/mcp_coder/workflows/implement/check_loop.py` — `_split_requests(binding)`,
  drop the `check_type_hints` parameter of `check_and_fix`
- `src/mcp_coder/workflows/implement/core.py` — drop `get_implement_config` and
  the `check_type_hints=` arguments
- `src/mcp_coder/workflows/implement/task_processing.py` — drop the
  `check_type_hints` parameters (two functions) and their forwarding
- **New** `src/mcp_coder/cli/commands/verify_toolkit_rows.py`
- `src/mcp_coder/cli/commands/verify_sections.py` — replace the old
  `check_type_hints` row (end of `_print_project_section`, pyproject branch)
  with a call to `check_type_hints_row`; drop the `get_implement_config` import
- `pyproject.toml` — delete the `[tool.mcp-coder.implement]` table (it only holds
  `check_type_hints = true`)
- Tests:
  - **new** `tests/cli/commands/test_verify_check_type_hints.py`
  - `tests/utils/test_pyproject_config.py` — replace the `get_implement_config`
    tests with `get_leftover_check_type_hints` tests
  - `tests/test_pyproject_config.py` — the assertion `check_type_hints is True`
    for this repo becomes "no leftover key" (`get_leftover_check_type_hints(root) is None`)
  - `tests/workflows/implement/**` — remove `get_implement_config` patches and
    `check_type_hints` arguments; delete tests of the dropped filter
  - `tests/cli/commands/test_verify.py::TestProjectSection` — the always-shown
    `check_type_hints` row is gone (edit in place; the file is near the size limit)

## WHAT

```python
# utils/pyproject_config.py
def get_leftover_check_type_hints(project_dir: Path) -> Any | None:
    """Return the retired [tool.mcp-coder.implement] check_type_hints value, or None if absent."""

# cli/commands/verify_toolkit_rows.py
def check_type_hints_row(project_dir: Path, symbols: dict[str, str], out: SectionBuilder) -> bool:
    """Add the retired-key row; False only for the error case."""

# workflows/implement/check_loop.py
def _split_requests(binding: Sequence[str]) -> tuple[list[str], list[str]]: ...
```

## HOW

- Reader style: like `has_legacy_format_code_key` (uses `_load_pyproject`,
  reads `tool.mcp-coder.implement`). TOML has no null, so `None` means absent.
- `verify_toolkit_rows.py` imports `load_toolkit_config` from
  `...utils.toolkit_runner`, `Row` from `.verify_formatting`, `SectionBuilder`
  from `.verify_render` — same one-directional shape as `verify_setup.py`.
- Row label `check_type_hints`, indent 4.

## ALGORITHM

```
value = get_leftover_check_type_hints(project_dir)
if value is None: return True                              # no key → no row
try: bindings = load_toolkit_config(project_dir).bindings
except ValueError: return True                             # Toolkit row already errors
fixes = {e: [r for r in bindings[e] if not r.startswith("check@")]
         for e in ("implement_task", "implement_final") if any(r.startswith("check@") for r in bindings[e])}
if value is False and fixes: add [ERR] row naming each `entry = json.dumps(fix)`; return False
add [WARN] row "retired; remove it"; return True
```

Error message, e.g.: `false is retired and checks now run; to keep skipping
them set under [tool.mcp-coder.toolkit.bindings]: implement_task = [],
implement_final = ["test@quick"]` (default bindings).

## DATA

- `get_leftover_check_type_hints` → raw TOML value or `None`.
- `check_type_hints_row` → `bool` (False only for the error case).

## Tests (write first)

- no key → no row, True
- `true` → `[WARN]` "retired; remove it", True
- `"no"` (non-bool) → `[WARN]`, True
- `false` + default bindings → `[ERR]` naming `implement_task = []` and
  `implement_final = ["test@quick"]`, False
- `false` + bindings `implement_task = []`, `implement_final = ["test@quick"]` → `[WARN]`, True
- `false` + broken toolkit table (e.g. `bogus = 1`) → no row, True
- check loop: a `check@*` request in the binding now always runs
