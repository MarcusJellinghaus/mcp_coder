# Summary — Coverage reporting, incl. diff-coverage (not a gate)

Issue: #1178. Epic: #1163.

## Goal

Add CI coverage reporting across the test suite, combined into one honest
number, with an advisory (never-blocking) diff-coverage percentage on pull
requests. No `--cov-fail-under` anywhere, on the combined number or the
diff-coverage number.

## Architecture / design changes

**CI job graph (`.github/workflows/ci.yml`).** The `test` matrix job
currently bundles `black`/`isort`/`pylint`/`ruff-docstrings`/`mypy`/
`file-size`/`no-url-deps`/`unit-tests`/`integration-tests` as matrix entries
under one job id. `unit-tests` and `integration-tests` move out into their
own standalone jobs — required because GitHub Actions `needs:` targets a
job id, not a matrix entry, and the new combine job must depend on them
directly. `langchain-integration.yml` (today a separate workflow file)
folds into `ci.yml` as a fourth standalone job, keeping its original
trigger restriction (push to `main`, or pull request) via an `if:` guard,
since `ci.yml` otherwise runs on push to every branch and this job makes
real, secrets-gated API calls.

A new `coverage` job depends on all three (`unit-tests`, `integration-tests`,
`langchain-integration`) and carries the *same* `if:` guard as the
langchain job. That's deliberate: it means the combine job only ever runs
when all three dependencies also ran, so there's no "artifact might be
missing" branch to handle. The trade-off is that plain feature-branch
pushes don't get a coverage summary — only PRs and pushes to `main` do.
That's an acceptable simplification: the langchain job doesn't run on
feature branches either, so a "combined" number without it there would
already be incomplete.

**Coverage data flow.** `unit-tests`, `integration-tests`, and
`langchain-integration` each run pytest with `--cov=src/mcp_coder
--cov-report=` (data file only, no per-job terminal report) and
`COVERAGE_FILE` set to a job-unique name (`.coverage.unit`,
`.coverage.integration`, `.coverage.langchain`), then upload that one file
as a build artifact (`coverage-data-unit`, etc.). The `coverage` job
downloads all three with `actions/download-artifact@v4`'s `pattern` +
`merge-multiple` into one flat directory, runs `coverage combine` then
`coverage xml`, giving one Cobertura `coverage.xml`. On pull requests it
additionally runs `diff-cover` against that XML, comparing to the PR base
branch, with its own native `--markdown-report` output — no percentage
parsing of diff-cover's own output; its report is just a lot included
in the step summary under our heading.

**New tool: `tools/ci_coverage_summary.py`.** A small, stdlib-only,
pure-function script that parses `coverage.xml`'s `<package>` elements,
rolls them up by top-level package name (first path segment under
`src/mcp_coder/`), and renders the `$GITHUB_STEP_SUMMARY` markdown:
headline %, the always-present marker-trap caveat text, a collapsed
`<details>` per-package table, and (when a diff-cover report is passed in)
an advisory diff-coverage section. Kept as a real, unit-tested Python file
— following the existing `tools/mlflow/*` convention of testing tools
scripts via `importlib.util.spec_from_file_location` — rather than
inline YAML/bash/awk, because the XML-grouping and markdown-formatting
logic is non-trivial enough to need real tests.

**Dependencies.** `pytest-cov` (test extra) and `diff-cover` (dev extra)
are both CLI/plugin-only — never `import`ed by `mcp_coder` — so both go
into `[tool.deptry.per_rule_ignores] DEP002`, the same bucket as
`pytest-asyncio`/`pytest-xdist`.

**Nothing gates.** No step anywhere passes `--cov-fail-under`. The
diff-cover step's exit code is not checked. The `coverage` job cannot fail
the build based on any coverage number.

## Files created

- `tools/ci_coverage_summary.py` — Cobertura XML parser + step-summary renderer.
- `tests/tools/test_ci_coverage_summary.py` — unit tests for the above.

## Files modified

- `pyproject.toml` — `pytest-cov`, `diff-cover`, DEP002 ignores.
- `.gitignore` — `.coverage`, `.coverage.*`, `coverage.xml`, `htmlcov/`.
- `.github/workflows/ci.yml` — job split, langchain fold-in, new `coverage` job.

## Files deleted

- `.github/workflows/langchain-integration.yml` — folded into `ci.yml`.

## Steps

1. [step_1.md](step_1.md) — `pyproject.toml` + `.gitignore`: declare `pytest-cov`/`diff-cover`.
2. [step_2.md](step_2.md) — `tools/ci_coverage_summary.py` (TDD): Cobertura parsing + summary rendering.
3. [step_3.md](step_3.md) — Split `unit-tests`/`integration-tests` out of the `test` matrix into standalone jobs, add `--cov` + artifact upload.
4. [step_4.md](step_4.md) — Fold `langchain-integration.yml` into `ci.yml` as a guarded job with `--cov` + artifact upload; delete the old workflow file.
5. [step_5.md](step_5.md) — New `coverage` job: combine, `coverage xml`, `diff-cover` on PRs, write the step summary.

Implementation order matters: step 1 (dependencies) before anything that
uses them; step 2 (the script) before step 5 (the job that calls it);
steps 3 and 4 (the jobs that produce the artifacts) before step 5 (the job
that consumes them).
