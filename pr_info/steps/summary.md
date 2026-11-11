# Summary — verify: per-section row renderer with automatic column width (#1409)

## Goal

`mcp-coder verify` output is meant to be column-aligned, but today the
marker/value columns shift 2 columns right per nesting level, and labels longer
than `_LABEL_WIDTH` (22) overrun their marker. Fix it by collecting each
section's rows as data and rendering the section once, with one label width
per section. Output must keep streaming section by section; exit codes and row
statuses do not change.

## Architectural / design changes

### 1. Column rule (in `verify_formatting.py`)

- A section's label width is
  `label_width = max(_LABEL_WIDTH, max(len(label) + indent - 2))` over its rows.
- Each row's label field is `label_width - (indent - 2)`. The prefix is
  `indent + label_field + " " + marker_slot(6) + " "`, so its length is
  `label_width + 10` **at every indent**: marker and value columns are
  identical within a section. Default value column: 32.
- `_format_row(label, marker, value, *, indent)` is a one-row section: minimum
  22, widened to its own label. Its `label_width` parameter goes away (step 6).
  `_format_row_prefix` keeps `label_width` (renderer-internal).

### 2. Rows are data — two shapes only (KISS)

```python
class Row(NamedTuple):          # verify_formatting.py
    label: str
    marker: str
    value: str
    indent: int = 2
    wrap: bool = False          # wrap value at 80 cols against the value column

Line = Row | str                # str = freeform line, passed through as-is
```

- **Tabular row** → `Row` (label and/or marker may be empty).
- **Hint / continuation line** → `_hint(text)` = `Row("", "", text)`. Because
  the prefix length does not depend on indent, an empty-label, empty-marker row
  starts exactly at the section's value column and never widens the section.
- **Group header** (`"  [Python]"`, `"  [Permissions]"`, `"  [github]"`),
  **blank line** (`""`) and **freeform line** → plain `str`.

This covers every line kind the issue lists with two renderer branches.

### 3. Renderer and builder (new `verify_render.py`)

- `_render_rows(lines: Sequence[Line]) -> list[str]` — computes the section
  width once, renders `Row`s through `_format_row_prefix`, wraps `wrap=True`
  rows with `textwrap.wrap(width=80, subsequent_indent=" " * len(prefix))`,
  passes `str` through.
- `SectionBuilder` — `open(title)`, `add(*lines)`, `close()`,
  `section(title, lines)`, context manager.
  - `open` closes any open section, then prints `_pad(title)` immediately.
  - `add` buffers while a section is open; with no section open, a `str`
    prints immediately and a `Row` prints via `_format_row`.
  - `close` renders and prints the buffered section (no-op when none open).
  - `__exit__` flushes the open section; if an exception is already
    propagating, a failure during the flush is logged and swallowed so the
    original exception wins.
  - Writes with `print` (resolves `sys.stdout` at call time → `capsys` works).
- Import direction: `verify_render → verify_formatting` only.
  `verify_formatting` never imports `verify_render`.

### 4. Formatters return rows

| Function | Before | After |
|---|---|---|
| `_format_section` | `(title, result, symbols) -> str` | `(result, symbols) -> list[Line]` |
| `_format_mcp_section` | `-> str` | `-> tuple[str, list[Line]]` (title, rows) |
| `_format_claude_mcp_section` | `-> str` | `-> tuple[str, list[Line]]` |
| `_format_tools_exposed_section` | `-> tuple[list[str], bool \| None]` | `-> tuple[list[Line], bool \| None]` |
| `_run_mcp_edit_smoke_test` (verify.py) | `-> str` | `-> Row` |

No string-returning wrapper is kept in production code.

### 5. Orchestration

- `execute_verify(args)` becomes a thin wrapper:
  `with SectionBuilder() as out: return _run_verify(args, out)`. The old body
  moves unchanged into `_run_verify` (no re-indent; patch targets unchanged).
- Every `print` in `verify.py` / `verify_sections.py` goes through `out`.
- Helpers in `verify_sections.py` take `out: SectionBuilder` as a parameter and
  keep their `_print_*` names. Helpers that own a whole section
  (`_print_environment_section`, `_print_project_section`,
  `_print_github_security_section`) open **and close** it themselves. Helpers
  that contribute rows to the caller's section (`_print_retired_env_var_warning`,
  `_print_langchain_readiness_warning`, `_format_code_row`, `_formatter_row`,
  `_toolkit_rows`) only `add`.
- The caller closes each section right after its last row, so no section waits
  on a slow call (e.g. LLM PROVIDER closes before `verify_langchain`).
- New `=== LLM TEST` section (smoke test, test prompt, tools-exposed rows,
  `--debug` line), opened only when `mcp_config_ok is not False`.

### 6. Label renames

- `Signing config consistent` → `Signing consistency`
- `Tool-calling capability` → `Tool-call capability`
- `MCP tools exposed to model` → `Tools exposed to model`

### 7. Removed

- `_VALUE_COLUMN_INDENT` (hints are now `_hint(...)` rows).
- `label_width=` on `_format_row` and every hand-set width in callers.

## Files

### Created

- `src/mcp_coder/cli/commands/verify_render.py` — `_render_rows`, `SectionBuilder`
- `tests/cli/commands/test_verify_label_map.py` — label renames / default-width fit (step 1)
- `tests/cli/commands/test_verify_render.py` — renderer + builder unit tests (steps 3–5)
- `tests/cli/commands/test_verify_config_width.py` — CONFIG section widening (step 6)
- `tests/cli/commands/test_verify_llm_test_section.py` — LLM TEST section, streaming test (step 7)

### Modified (production)

- `src/mcp_coder/cli/commands/verify_formatting.py` — `Row`, `Line`, `_hint`,
  `_section_label_width`, new prefix rule, formatters return rows, renames
- `src/mcp_coder/cli/commands/verify.py` — `_run_verify`, builder wiring,
  LLM TEST, smoke test returns `Row`
- `src/mcp_coder/cli/commands/verify_sections.py` — helpers take `out`
- `docs/cli-reference.md` — LLM TEST in the verify section list

### Modified (tests)

- `tests/cli/commands/conftest.py` — `_expected_value_column`, `_render`,
  `_assert_section_aligned`, `_assert_sections_aligned`, `_SMOKE_ROW`,
  `_mock_print_project_section`, env-var autouse fixture, indent-6 toolkit fixture
- `tests/cli/commands/test_verify_format_pad.py`
- `tests/cli/commands/test_verify.py` (edits must be net line-neutral; file is at 743/750)
- `tests/cli/commands/test_verify_alignment.py`
- `tests/cli/commands/test_verify_format_section_basic.py`
- `tests/cli/commands/test_verify_format_mcp_section.py`
- `tests/cli/commands/test_verify_tools_exposed.py`
- `tests/cli/commands/test_verify_jenkins.py`
- `tests/cli/commands/test_verify_mcp_orchestration.py`
- `tests/cli/commands/test_verify_mcp_edit_smoke.py`
- `tests/cli/commands/test_verify_orchestration.py`
- `tests/cli/commands/test_verify_orchestration_env.py`
- `tests/cli/commands/test_verify_sections_orchestration.py`
- `tests/cli/commands/test_verify_sections_config.py`
- `tests/cli/commands/test_verify_sections_security.py`
- `tests/cli/commands/test_verify_github_security_probe.py`
- `tests/cli/commands/test_verify_project_section.py`
- `tests/llm/providers/langchain/test_langchain_contract_rows.py`

## Steps

1. Label renames.
2. Row model + per-section width formula in `verify_formatting`.
3. `verify_render.py`: renderer + `SectionBuilder` (additive) + shared test helpers.
4. Formatters return rows; `execute_verify` drives a `SectionBuilder`.
5. `verify_sections` helpers write through the builder; drop `_VALUE_COLUMN_INDENT`.
6. `verify.py` inline sections write through the builder; smoke test returns `Row`; drop `label_width` from `_format_row`.
7. `=== LLM TEST` section + docs + streaming test.
8. Per-section alignment tests incl. indent 6.

Each step leaves the full check suite green. Between steps 4 and 6, sections
not yet migrated still `print` directly; this is safe because every migrated
section is opened and closed atomically (`out.section(...)`), so no raw `print`
ever happens while a section is buffered.

## Constraints to keep in mind in every step

- Never buffer the whole run; a section renders as soon as it is closed.
- No direct `print` while a section is open — including in test doubles.
- File size limit 750 lines; `test_verify.py` is at 743 — keep its edits
  net-neutral. New tests go into new files.
- Run after each step: `run_pylint_check`, `run_pytest_check` (with
  `-n auto` and the fast-unit marker filter from CLAUDE.md), `run_mypy_check`,
  `run_lint_imports_check`, `run_vulture_check`; format with `run_format_code`.
