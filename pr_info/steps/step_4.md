# Step 4 — Formatters return rows; `execute_verify` drives a `SectionBuilder`

## LLM prompt

> Read `pr_info/steps/summary.md` (sections 4 and 5) and this file. Implement
> step 4 only: the four `verify_formatting` formatters return rows instead of
> strings, `execute_verify` becomes a thin wrapper around `_run_verify(args, out)`,
> and every caller of those formatters renders through the builder. Other
> `print` calls in `verify.py` / `verify_sections.py` stay for now (steps 5–6).
> Update the tests that read formatter output as strings. Tests first, then
> code. Run pylint, pytest (fast unit filter, `-n auto`), mypy, lint-imports;
> all must pass. One commit.

## Precondition

Only `verify.py` and `verify_sections.py` call the four formatters in
production (other `src/` hits are docstrings). If a search for
`_format_section(`, `_format_mcp_section(`, `_format_claude_mcp_section(` or
`_format_tools_exposed_section(` finds another production caller, write one
line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/cli/commands/verify_formatting.py`
- `src/mcp_coder/cli/commands/verify.py`
- `src/mcp_coder/cli/commands/verify_sections.py` (`_print_github_security_section` only)
- tests listed below

## WHAT

```python
# verify_formatting.py
def _format_section(result: dict[str, Any], symbols: dict[str, str]) -> list[Line]: ...
def _format_mcp_section(mcp_results, symbols, *, list_mcp_tools=False,
                        for_completeness=False) -> tuple[str, list[Line]]: ...
def _format_claude_mcp_section(statuses, symbols, *,
                               for_completeness=False) -> tuple[str, list[Line]]: ...
def _format_tools_exposed_section(system_message, symbols) -> tuple[list[Line], bool | None]: ...

# verify.py
def execute_verify(args: argparse.Namespace) -> int:
    """(docstring unchanged)"""
    with SectionBuilder() as out:
        return _run_verify(args, out)

def _run_verify(args: argparse.Namespace, out: SectionBuilder) -> int:
    """Body of execute_verify; writes sections through *out*."""

# verify_sections.py
def _print_github_security_section(project_dir: Path, symbols: dict[str, str],
                                   out: SectionBuilder) -> None: ...
```

## HOW — formatter conversions

`_format_section` (drop `title`, keep every rule):
- regular / branch-protection child / perm rows → `Row(label, symbol, row_value, indent)`;
  `strict_mode` → `Row(label, "", value, 4)`.
- `[Permissions]` header → append `""` then `"  [Permissions]"` (plain `str`).
- token source line → `_hint(f"from {suffix}")`; install hint →
  `_hint(f"-> {entry['install_hint']}")`.
- Values still rendered with `str(entry.get("value", ""))` (`None` → `"None"`).

`_format_mcp_section`:
- title computed exactly as today; return `(title, lines)`.
- list mode: server row `Row(name, symbol, f"{n} tools available")`; tool
  detail lines stay plain `str` (`f"    {tool_name:<{max_name + 2}s} {desc}"`).
- non-list mode with tools: `Row(name, symbol, tools_text, wrap=True)` (drop the
  local `textwrap` use; the renderer wraps). Remove the `textwrap` import if unused.

`_format_claude_mcp_section`: `(title, [Row(status.name, symbol, status.status_text) ...])`.

`_format_tools_exposed_section`: `Row(label, marker, value)` plus `_hint(hint)` /
`_hint(note)` instead of `_VALUE_COLUMN_INDENT` strings. Docstring: "lines" → "rows".

## HOW — callers

`verify.py` (`_run_verify` body = old `execute_verify` body, moved unchanged
except for these lines):
- `print(_format_section("GIT", git_result, symbols))` →
  `out.section("GIT", _format_section(git_result, symbols))`; same for
  GITHUB, JENKINS, JENKINS JOBS, BASIC VERIFICATION, LLM PROVIDER DETAILS, MLFLOW.
- `print(_format_claude_mcp_section(...))` → `out.section(*_format_claude_mcp_section(...))`;
  same for `_format_mcp_section`.
- tools exposed: `tools_rows, tools_exposed_ok = ...; out.add(*tools_rows)`
  (no section is open there yet → each row prints immediately, same output as today).
- `_print_github_security_section(project_dir, symbols, out)`.

`verify_sections.py`: `_print_github_security_section` builds the dict exactly
as today (calling `verify_github_security` **before** opening anything), then
`out.section("GITHUB SECURITY", _format_section(github_security_result, symbols))`.

Every `out.section(...)` opens and closes atomically, so the remaining raw
`print` calls never run while a section is buffered.

## Tests (write first / update)

Use the conftest helpers from step 3 (`_render`, `_assert_section_aligned`).

- `test_verify_format_section_basic.py` (706 lines — keep net line count ≤ 0):
  `_format_section("X", result, self._symbols())` → `_render(_format_section(result, self._symbols()))`;
  delete `test_section_title_in_header`; hint asserts use
  `f"{' ' * _expected_value_column()}-> pip install langchain-openai"`
  (drop `_VALUE_COLUMN_INDENT` import). `[Permissions]` tests: GITHUB now widens
  to value column 33, so replace `_format_row(label, ..., indent=4) in output`
  with: the line starting with `f"    {label} "` contains the marker and value, plus
  `_assert_section_aligned(output)`. `test_perm_workflows_read_label_aligns_at_label_width`
  → assert `_assert_section_aligned(output)` and that `Actions: Read` sits at indent 4.
- `test_verify_format_mcp_section.py`: unpack `title, lines = ...`; assert on
  `_render(lines)`; title asserts move to `title`. Tools-exposed tests: `_render(lines)`.
  Add: non-list mode with many tools → all lines ≤ 80 chars and continuation
  lines start at the section's value column.
- `test_verify_tools_exposed.py`: `text = _render(lines)`.
- `test_verify_alignment.py`: per-formatter tests feed `_render(...)` of the new
  return values into the existing `_assert_aligned_by_indent` (rewritten in step 8).
- `test_verify_jenkins.py` (~532, ~547): `rendered = _render(_format_section(..., STATUS_SYMBOLS))`.
- `test_verify_mcp_orchestration.py` (~174, `test_mcp_section_header_includes_library_name`):
  `title, _lines = _format_mcp_section(mcp_result, symbols)`; assert on `title`.
- `test_verify_sections_security.py` (~383) and
  `test_verify_github_security_probe.py` (~33): pass `SectionBuilder()` as `out`.
- `tests/llm/providers/langchain/test_langchain_contract_rows.py` `_row`:
  `section = _render_rows(_format_section(result, STATUS_SYMBOLS))` (import from
  `mcp_coder.cli.commands.verify_render`); iterate the list directly.
- New test (in `tests/cli/commands/test_verify_render.py`): GITHUB result with
  `[Permissions]` rows renders all rows aligned (value column 33) and the
  `from GITHUB_TOKEN env var` hint starts at that column.

## DATA

- `list[Line]`: `Row` for tabular rows and hints, `str` for `""`,
  `"  [Permissions]"` and `--list-mcp-tools` detail lines.
- MCP formatters: `(title, lines)`; tools-exposed: `(lines, ok)` with `ok`
  semantics unchanged.
