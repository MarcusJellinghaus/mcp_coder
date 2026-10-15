# Step 1 — Declare `pytest-cov` and `diff-cover`, ignore their coverage artifacts

See [summary.md](summary.md) for the overall design.

## WHERE

- `pyproject.toml`
- `.gitignore`

## WHAT

No new functions — this step only changes dependency declarations and
ignore patterns.

- `pyproject.toml`: `[project.optional-dependencies] test` gains
  `"pytest-cov"`. `[project.optional-dependencies] dev` gains
  `"diff-cover"` (it already pulls in `test` transitively via
  `mcp-coder[types,test,langchain,mlflow,tui]`).
- `pyproject.toml`: `[tool.deptry.per_rule_ignores] DEP002` gains
  `"pytest-cov"` and `"diff-cover"`, in the "mcp_coder only; no sibling
  provides them" group alongside `"deptry"`, `"pytest-textual-snapshot"`,
  `"textual-dev"`.
- `.gitignore`: add `.coverage`, `.coverage.*`, `coverage.xml`, `htmlcov/`
  (new section, e.g. under a `# Coverage artifacts` comment).

## HOW

Plain TOML/gitignore edits via `mcp__mcp-workspace__edit_file`. No code
imports anything from `pytest-cov` or `diff-cover` — both are CLI-only,
which is exactly why they need the DEP002 ignore.

## ALGORITHM

N/A — declarative config only.

## DATA

N/A.

## Verification

- Run `mcp__mcp-tools-py__run_pytest_check` with the fast-unit selection —
  must still pass (installing `pytest-cov` must not break anything else).
- Run `mcp__mcp-tools-py__run_format_code`, then the standard checks
  (`pylint`, `pytest`, `mypy`) from CLAUDE.md. `deptry` is run from the
  `architecture` CI job, not locally in these checks, so no local deptry
  verification is required for this step.

## Precondition that may not hold

If installing `pytest-cov` or `diff-cover` into the project's dependency
set produces an unresolvable version conflict (surfaced by the install
step failing, not by the checks above), write one line to
`pr_info/.blocked.txt` and stop.

## Commit

One commit: both file edits together, message e.g.
`deps(coverage): add pytest-cov and diff-cover`.

## LLM prompt

> Implement Step 1 of [summary.md](summary.md) — add `pytest-cov` to the
> `test` extra and `diff-cover` to the `dev` extra in `pyproject.toml`,
> add both to `[tool.deptry.per_rule_ignores] DEP002`, and add
> `.coverage`, `.coverage.*`, `coverage.xml`, `htmlcov/` to `.gitignore`.
> No code changes. Run the project's standard checks (pylint, pytest,
> mypy) and commit as one commit. If the dependency install itself fails
> with an unresolvable conflict, write one line to `pr_info/.blocked.txt`
> and stop.
