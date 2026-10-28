# Step 2 — The pydeps scripts write to `docs/architecture/dependencies/`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> This is a mechanical path replacement in the pydeps scripts and the committed viewer snippet.
> Make no other edits. Run the checks below, then make one commit.

## WHERE
- `tools/pydeps_graph.sh`
- `tools/pydeps_graph.bat`
- `docs/architecture/dependencies/pydeps_graph.html` (the `<pre><code>` command snippet only)

## WHAT
No functions. Path strings only.

## HOW
Replace every occurrence (header comments, `mkdir`, both `pydeps` output paths, every
`echo` line):
- `.sh`: `docs/architecture/pydeps_graph` → `docs/architecture/dependencies/pydeps_graph`;
  `mkdir -p docs/architecture` → `mkdir -p docs/architecture/dependencies`.
- `.bat`: the same for `docs/architecture/pydeps_graph`; `docs\architecture\pydeps_graph`
  → `docs\architecture\dependencies\pydeps_graph`;
  `if not exist "docs\architecture" mkdir "docs\architecture"`
  → `if not exist "docs\architecture\dependencies" mkdir "docs\architecture\dependencies"`.
- `pydeps_graph.html`: `-o docs/architecture/pydeps_graph.svg`
  → `-o docs/architecture/dependencies/pydeps_graph.svg`.

## ALGORITHM
None.

## DATA
Outputs: `docs/architecture/dependencies/pydeps_graph.dot` (committed) and `pydeps_graph.svg`
(generated, needs GraphViz).

## Checks
- `search_files(pattern="docs[/\\\\]architecture[/\\\\]pydeps_graph")` returns no hits outside `pr_info/`
- `run_format_code` (no Python changes expected)

## Commit
`fix(tools): write pydeps graph to docs/architecture/dependencies`
