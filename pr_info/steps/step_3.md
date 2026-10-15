# Step 3 — Split `unit-tests`/`integration-tests` into standalone jobs, add coverage

See [summary.md](summary.md) for the overall design.

## WHERE

`.github/workflows/ci.yml`

## WHAT

No Python functions — this step edits workflow YAML.

- Remove the `unit-tests` and `integration-tests` entries from the `test`
  job's `matrix.check` list (the matrix keeps `black`, `isort`, `pylint`,
  `ruff-docstrings`, `mypy`, `file-size`, `no-url-deps`).
- Add two new standalone jobs, `unit-tests` and `integration-tests`, each
  with the same checkout/`astral-sh/setup-uv`/`actions/setup-python`/
  install steps the `test` matrix jobs use today
  (`uv pip install --system "${SPECS[@]}" ".[dev,langchain]"` via
  `tools/read_github_deps.py --specs`).
- Each job's pytest step keeps its existing marker selection (copied
  verbatim from today's matrix `cmd` values) and adds
  `--cov=src/mcp_coder --cov-report=` plus `--junitxml=<job>.xml` (as
  today). Set `COVERAGE_FILE: .coverage.unit` (or `.coverage.integration`)
  as a step-level `env:` entry.
- Each job uploads its coverage data file as a build artifact:
  `actions/upload-artifact@v4`, `name: coverage-data-unit` (or
  `coverage-data-integration`), `path: .coverage.unit` (or
  `.coverage.integration`), `retention-days: 1` (short-lived — the
  `coverage` job in step 5 consumes it within the same workflow run).

## HOW

Plain YAML edit, no composite action introduced — matches the existing
convention of repeating the checkout/setup/install steps per job/matrix
entry (see `architecture`, `vscodeclaude-template-install`, and the
`test` matrix itself, all of which already repeat this boilerplate).

## ALGORITHM

N/A — no new logic, just job restructuring.

## DATA

N/A.

## Verification

- Locally run the *exact* marker selections the two new jobs will use via
  `mcp__mcp-tools-py__run_pytest_check`, confirming both still pass (they
  already do today under the `test` matrix; this just confirms nothing
  about the `--cov` flag breaks collection).
- `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_mypy_check`
  (these two new jobs don't touch src/tests code, so these should be
  unaffected, but are still run per CLAUDE.md's standard checks).
- No automated YAML test exists in this repo; correctness of the workflow
  itself is confirmed once the PR's Actions run completes (visible via
  `mcp__mcp-workspace__check_branch_status` after pushing), not by a local
  test in this step.

## Commit

One commit: the full `ci.yml` restructuring (matrix shrink + two new
jobs), message e.g.
`ci: split unit-tests/integration-tests into standalone jobs with coverage`.

## LLM prompt

> Implement Step 3 of [summary.md](summary.md). In
> `.github/workflows/ci.yml`, remove the `unit-tests` and
> `integration-tests` entries from the `test` job's matrix, and add them
> back as two standalone jobs with the same install steps used elsewhere
> in this file, each running its existing pytest marker selection plus
> `--cov=src/mcp_coder --cov-report=`, writing to a job-unique
> `COVERAGE_FILE`, and uploading that file as a build artifact named
> `coverage-data-unit` / `coverage-data-integration`. Run the project's
> standard checks and commit as one commit.
