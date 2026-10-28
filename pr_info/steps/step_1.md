# Step 1 — `tach_docs.py` writes to `docs/architecture/dependencies/`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> TDD: update the test first, watch it fail, then fix `tools/tach_docs.py` and the header comments.
> Run the checks listed below, then make one commit.

## WHERE
- `tests/tools/test_tach_docs.py`
- `tools/tach_docs.py`
- `tools/tach_docs.sh`, `tools/tach_docs.bat` (header comments only)

## WHAT
- No new functions. `main() -> int` in `tools/tach_docs.py` keeps its signature.
- Test `test_main_writes_no_crlf_bytes` asserts the new output directory.

## HOW
1. **Test first:** in `tests/tools/test_tach_docs.py` change
   `out = tmp_path / "docs" / "architecture"` to
   `out = tmp_path / "docs" / "architecture" / "dependencies"`.
   Run the test. It must fail (the files are not found).
2. `tools/tach_docs.py`:
   - `output_dir = Path(__file__).parent.parent / "docs" / "architecture" / "dependencies"`
   - module docstring: `docs/architecture/dependency_graph.html` and `dependency_report.html`
     → `docs/architecture/dependencies/...`
   - final print → `"\nDone! Open docs/architecture/dependencies/dependency_graph.html to view."`
3. `tools/tach_docs.sh` / `.bat` header comments: `docs/architecture/dependency_*.html`
   → `docs/architecture/dependencies/dependency_*.html`.

## ALGORITHM
None. This is a path change: `mkdir(parents=True, exist_ok=True)` already creates the subdirectory.

## DATA
Output files: `docs/architecture/dependencies/dependency_graph.html` (committed) and
`docs/architecture/dependencies/dependency_report.html` (gitignored, `.gitignore:52`).

## Checks
- `run_pytest_check(extra_args=["-n", "auto", "tests/tools/test_tach_docs.py"])` passes
- `run_format_code`, `run_pylint_check`, `run_mypy_check`, fast unit-test suite
- `search_files(pattern="docs/architecture/dependency_", glob="tools/**")` returns no hits

## Commit
`fix(tools): write tach_docs output to docs/architecture/dependencies`
