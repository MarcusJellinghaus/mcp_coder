# Step 2 — `tools/ci_coverage_summary.py`: parse Cobertura XML, render the step summary

See [summary.md](summary.md) for the overall design.

## WHERE

- `tools/ci_coverage_summary.py` (new)
- `tests/tools/test_ci_coverage_summary.py` (new)

## WHAT

```python
MARKER_TRAP_CAVEAT: str  # constant text naming the markers that never run in CI

@dataclass
class PackageRollup:
    name: str
    lines_valid: int
    lines_covered: int
    @property
    def rate(self) -> float: ...

@dataclass
class CoverageSummary:
    lines_valid: int
    lines_covered: int
    packages: list[PackageRollup]
    @property
    def rate(self) -> float: ...

def top_level_package_name(full_name: str) -> str: ...
def parse_coverage_xml(xml_path: Path) -> CoverageSummary: ...
def render_step_summary(summary: CoverageSummary, diff_report: str | None) -> str: ...
def main(argv: list[str] | None = None) -> int: ...
```

`main` parses `--coverage-xml PATH` (required), `--diff-report PATH`
(optional — a markdown file produced by `diff-cover`, read verbatim if
present), and `--output PATH` (defaults to `$GITHUB_STEP_SUMMARY`, falling
back to stdout if that env var is unset — keeps the script runnable
outside CI). It appends the rendered markdown to `--output`.

## HOW

Standalone script, no project imports, stdlib only
(`xml.etree.ElementTree`, `argparse`, `dataclasses`, `pathlib`, `os`,
`sys`). Follows the existing `tools/mlflow/*` convention: pure functions
over parsed data, no CLI side effects except in `main`. Tests load the
module the same way `tests/tools/mlflow/test_analyze_permission_events.py`
does — via `importlib.util.spec_from_file_location` — since `tools/` is
not import-path-friendly from `pythonpath = ["src"]`.

## ALGORITHM

`top_level_package_name(full_name)`: split on `.`; if the first segment is
`mcp_coder` and there's a second segment, return the second segment
(`"mcp_coder.llm.providers"` → `"llm"`); otherwise return the first
segment (a loose top-level module's Cobertura package name is just
`"mcp_coder"`, grouped as its own bucket).

`parse_coverage_xml(xml_path)`: for every `<package>` element, find its
top-level bucket name; walk every `<class><lines><line hits="…"/>` under
that package and count total lines (valid) and lines with `hits != "0"`
(covered); accumulate per-bucket `PackageRollup` totals and a grand total.
Summing from `<line>` elements (not any `line-rate`/count attribute on
`<package>`) avoids depending on exactly which raw-count attributes a
given coverage.py version puts on `<package>` — only the universally
present `<line hits="…">` elements are load-bearing.

`render_step_summary(summary, diff_report)`: headline `## Coverage: X%`,
the caveat text, a collapsed `<details><summary>Per-package
breakdown</summary>` table (one row per `PackageRollup`, sorted by name),
and — only when `diff_report` is not `None` — a bold "Diff coverage
(advisory, not a gate)" heading followed by the report text verbatim.

## DATA

`CoverageSummary.rate` / `PackageRollup.rate` are `covered / valid` (`0.0`
when `valid == 0`). `render_step_summary` returns one markdown string;
`main` appends it to the output file with a trailing newline.

## Before writing the parser: confirm the real Cobertura schema

Don't assume the exact attribute/element names from memory. In a
throwaway `.scratch/` probe: `pip install coverage` into an isolated venv,
run a trivial module through `coverage run` + `coverage xml` on a toy
3-4-line Python file, and open the resulting XML to confirm the
`<package>`/`<class>`/`<lines>/<line hits="…">` structure this step
assumes. Adjust `parse_coverage_xml` to match what's actually produced.
Delete `.scratch/` when done.

## Precondition that may not hold

If a real `coverage xml` run does not produce `<line hits="…">` elements
nested under `<package>/<classes>/<class>/<lines>` at all (i.e. the
structure this step's algorithm assumes doesn't exist in the installed
coverage.py version), write one line to `pr_info/.blocked.txt` and stop.

## Verification

Unit tests (write first, then the implementation):

- `test_top_level_package_name_...` — root module, nested module, loose
  top-level module.
- `test_parse_coverage_xml_aggregates_by_top_level` — small XML fixture
  (string, written to `tmp_path`) with two packages sharing a top-level
  bucket and one in a different bucket; assert summed valid/covered counts.
- `test_render_step_summary_includes_caveat_and_table`
- `test_render_step_summary_omits_diff_section_when_none`
- `test_main_writes_markdown_to_output_file` — `tmp_path`, no
  `GITHUB_STEP_SUMMARY` env var, asserts `--output` file contents.

Then run `mcp__mcp-tools-py__run_pytest_check` scoped to
`tests/tools/test_ci_coverage_summary.py`, then the full fast-unit
selection, `pylint`, `mypy`.

## Commit

One commit: tests + implementation together, message e.g.
`feat(ci): add ci_coverage_summary tool for coverage step summary`.

## LLM prompt

> Implement Step 2 of [summary.md](summary.md). Write
> `tests/tools/test_ci_coverage_summary.py` first (loading the module via
> `importlib.util.spec_from_file_location`, matching the pattern in
> `tests/tools/mlflow/test_analyze_permission_events.py`), covering
> `top_level_package_name`, `parse_coverage_xml`, `render_step_summary`,
> and `main`, then implement `tools/ci_coverage_summary.py` per the
> WHAT/ALGORITHM sections of this step. Before finalizing the XML parser,
> confirm the real Cobertura schema via a `.scratch/` probe as described,
> then delete `.scratch/`. Run the project's standard checks and commit as
> one commit. If the probe shows the assumed `<line hits>` structure
> doesn't exist, write one line to `pr_info/.blocked.txt` and stop.
