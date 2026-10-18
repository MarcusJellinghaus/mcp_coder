# Step 8: LF-only writes in `tools/tach_docs.py`

See `pr_info/steps/summary.md` for the full design rationale. Independent of
all other steps — it does **not** use `write_lf_text` (`tools/` is a
stand-alone dev script and must not depend on `src/`).

## Precondition

`tools/tach_docs.py` must still contain, inside `main`, exactly these two
lines:

```python
    graph_path.write_text(graph_html, encoding="utf-8")
```

```python
    report_path.write_text(report_html, encoding="utf-8")
```

If either line is not found verbatim, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- Modify `tools/tach_docs.py`
- Create `tests/tools/test_tach_docs.py`

## WHAT

Add one small module-level function above `main` and use it for both writes:

```python
def _write_lf(path: Path, text: str) -> None:
    """Write text with LF-only line endings (the HTML files are committed)."""
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
```

`Path.write_text(newline=...)` needs Python 3.10+ (`requires-python =
">=3.11"`). Passing `newline="\n"` alone only disables translation; it does
not strip an embedded `\r\n`, hence the explicit `replace`.

`main()`'s behaviour, output paths, and return value are unchanged.

## HOW

- Replace the two Precondition lines with `_write_lf(graph_path, graph_html)`
  and `_write_lf(report_path, report_html)`.
- No imports from `mcp_coder` — only the existing `pathlib.Path` import.

## ALGORITHM

Not applicable.

## DATA

The two generated files (`docs/architecture/dependency_graph.html`,
`dependency_report.html`) contain LF-only bytes.

## Tests (write first)

Create `tests/tools/test_tach_docs.py`. Load the script the same way
`tests/tools/test_ci_coverage_summary.py` does (`importlib.util.spec_from_file_location`
on `tools/tach_docs.py`). Before writing it, confirm the module has no
import-time side effects (it should be import-safe; if not, write one line to
`pr_info/.blocked.txt` and stop).

```python
def test_main_writes_no_crlf_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Generated HTML has LF-only bytes even if the generators emit CRLF."""
    monkeypatch.setattr(tach_docs, "__file__", str(tmp_path / "tools" / "tach_docs.py"))
    monkeypatch.setattr(tach_docs, "get_mermaid_diagram", lambda: "graph")
    monkeypatch.setattr(
        tach_docs, "generate_graph_html", lambda _diagram: "<html>\r\ngraph\r\n</html>\r\n"
    )
    monkeypatch.setattr(tach_docs, "get_dependency_report", lambda _module: "report")
    monkeypatch.setattr(
        tach_docs, "generate_report_html", lambda _reports: "<html>\r\nreport\r\n</html>\r\n"
    )

    assert tach_docs.main() == 0

    out = tmp_path / "docs" / "architecture"
    for name in ("dependency_graph.html", "dependency_report.html"):
        assert b"\r" not in (out / name).read_bytes()
```

`main()` derives its output directory from `Path(__file__).parent.parent`,
so patching the module's `__file__` redirects it into `tmp_path` and the real
`docs/architecture/` is never touched. Check the real signatures of
`get_mermaid_diagram`, `generate_graph_html`, `get_dependency_report` and
`generate_report_html` in `tools/tach_docs.py` and adjust the lambdas to
match. Injecting `\r\n` makes the test fail on every OS against the current
`write_text` code.

Write the test first, confirm it fails, then apply the implementation change.

## Checks

Run, in order, and fix anything that fails before committing:

- `mcp__mcp-tools-py__run_pytest_check`, scoped to
  `tests/tools/test_tach_docs.py`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_tach_check`
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-tools-py__run_format_code`

## Commit

One commit: `fix(tools): write tach_docs HTML output with LF-only line endings`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_8.md`). Implement Step 8 exactly as specified: create
> `tests/tools/test_tach_docs.py` first, confirm it fails, then add
> `_write_lf` to `tools/tach_docs.py` and use it for both writes. Do not
> import anything from `mcp_coder` in `tools/tach_docs.py`. If the
> precondition in this file does not hold, write one line to
> `pr_info/.blocked.txt` and stop — do not improvise a different fix. Run
> the checks listed under "Checks" and fix any failures. Format code, then
> make exactly one commit for this step.
