# Step 1 — Split CI by event and document it

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Edit only the three files listed below. Do not rename any matrix entry `name`, and do not add
> step-level `if:` conditions. Run the checks listed under **Checks**, then commit as one commit.

## Precondition

`.github/workflows/ci.yml` has a `test` matrix job (containing `pylint`) and an `architecture`
matrix job (containing `import-linter`, `tach`, `vulture`, `deptry`, `if: github.event_name ==
'pull_request'`). If either is missing or differs, write one line to `pr_info/.blocked.txt`
naming the mismatch and stop.

## Tests

No Python changes, so no unit tests (TDD not applicable). No tool validates workflow YAML
locally; the CI run on the pushed branch is the syntax check.

---

## Part A — `.github/workflows/ci.yml`

### WHERE
`.github/workflows/ci.yml` (only this workflow).

### WHAT
1. **Header**, between `name: Python CI` and `on:`:
   ```yaml
   # Which job runs on which event:
   #   Feature push  → first-line checks + tests: fast, catch most errors early.
   #   Pull request  → backup checks + tests: slow, or redundant with earlier gates.
   #   Main push / dispatch → both sets (post-merge safety net).
   # Every check runs at least once before merge, on push or on PR.
   # Job names are required-check names: don't rename them, and never skip a check with a step-level `if`.
   ```
2. **`check-forbidden-folders`**: add the comment above the job, condition unchanged:
   ```yaml
   # PR only: pr_info/ is allowed on branches, not in a merge.
   ```
3. **`test` → `push-checks`**: rename the job id in place and keep the existing
   "Matrix approach… / fail-fast…" comment above it. Then add
   `# First-line checks: run on every push, not again on the PR.`
   and `if: github.event_name != 'pull_request'` (after `runs-on`).
   Matrix entries, in this order:
   - `ruff-format`, `ruff`, `mypy` (keeps `install: ".[typecheck]"`), `file-size`,
     `no-url-deps`, `forbidden-calls`: unchanged lines from `test`
   - `pylint`: **removed** (moves to `pr-checks`)
   - `import-linter`, `vulture`: **added**, lines copied verbatim from `architecture`

   Steps unchanged.
4. **`pr-checks`**: delete the `architecture` job (and its two
   "Architecture checks - only run on pull requests" / "These validate…" comment lines).
   Add a new job directly after `push-checks`, with the same steps as `architecture`:
   ```yaml
   # Backup checks: run on PR, main push and dispatch.
   pr-checks:
     runs-on: ubuntu-latest
     if: github.event_name != 'push' || github.ref == 'refs/heads/main'
     strategy:
       fail-fast: false
       matrix:
         check:
           - {name: "pylint", cmd: "pylint --version && pylint ./src ./tests"}  # configuration via pyproject.toml
           - {name: "tach", cmd: "tach --version && ./tools/tach_check.sh"}
           - {name: "deptry", cmd: "deptry --version && ./tools/deptry_check.sh"}
     name: ${{ matrix.check.name }}
     steps:  # identical to the old `architecture` steps (checkout, uv, python 3.11,
             # install `.[dev,langchain]` with SPECS, environment info, run cmd)
   ```
   Use the same `matrix.check.install || '.[dev,langchain]'` install line as `push-checks`, so
   both matrices share one step block shape.
5. **`unit-tests`** and **`integration-tests`**: add the comment above each job, no condition:
   ```yaml
   # Runs on push and PR: coverage needs it in the PR run.
   ```
6. **`vscodeclaude-template-install`**:
   - Add `# Backup checks: run on PR, main push and dispatch.` as the first comment line and
     `if: github.event_name != 'push' || github.ref == 'refs/heads/main'` after `runs-on`.
   - Reword "Independent of `test` because it uses an activated project venv…" to
     "Not a matrix entry because it uses an activated project venv…" (rest of the sentence
     unchanged), so it no longer names a job id.
7. Unchanged: triggers, `langchain-integration`, `coverage`, all step contents.

### HOW
Job-level `if:` only. GitHub skips the whole matrix job without expanding it, so a skipped
matrix shows as one check under the unexpanded name.

### ALGORITHM (event → jobs)
```
push to feature branch  → push-checks, unit-tests, integration-tests
pull_request            → pr-checks, vscodeclaude-template-install, unit-tests, integration-tests,
                          check-forbidden-folders, langchain-integration, coverage
push to main            → everything except check-forbidden-folders
workflow_dispatch       → push-checks, pr-checks, template-install, unit-tests, integration-tests
```

### DATA
Required-check names unchanged: ruff-format, ruff, mypy, file-size, no-url-deps,
forbidden-calls, vulture, import-linter, pylint, tach, deptry, unit-tests, integration-tests,
vscodeclaude-template-install, check-forbidden-folders, langchain-integration, coverage.

---

## Part B — `docs/repository-setup/quality-and-security-checks.md`

### WHERE
New section `## CI events` between `## Tool support` and `## Lint`. Edits in `## Architecture`
and `## Dependencies`.

### WHAT
1. Insert:
   ```markdown
   ## CI events

   Which [`ci.yml`](../../.github/workflows/ci.yml) job runs on which event. First-line checks run
   on feature-branch push: fast, they catch most errors early. Backup checks run on the PR: slow,
   or redundant with earlier gates. Every check runs at least once before merge (#1354).

   | Job | Feature push | PR | Main push / dispatch | Why |
   |---|---|---|---|---|
   | ruff-format, ruff, mypy, file-size, no-url-deps, forbidden-calls, vulture, import-linter | ✅ | — | ✅ | First-line: no automated gate before CI (mypy, ruff-format also run in `implement`); the push run covers the PR |
   | unit-tests, integration-tests | ✅ | ✅ | ✅ | Every event: `coverage` needs them in the PR run; integration markers are excluded locally |
   | pylint | — | ✅ | ✅ | Backup: ruff is the main linter (#1163); pylint also runs locally per task and in `mcp-coder rebase` |
   | tach, deptry | — | ✅ | ✅ | Backup: rarely triggered |
   | vscodeclaude-template-install | — | ✅ | ✅ | Backup: its inputs (installer, `pyproject.toml`, sibling HEADs) rarely change |
   | check-forbidden-folders | — | ✅ | — | `pr_info/` is allowed on branches, not in a merge |
   | langchain-integration, coverage | — | ✅ | main push only | Calls real LLM APIs; `coverage` combines the test jobs of its own run and updates the badge on main |
   ```
2. `## Architecture`: replace the first two sentences ("import-linter … run in the PR-only
   `architecture` matrix (deptry too, …). Pylint `R0401` catches cyclic imports on every push.")
   with:
   ```markdown
   import-linter ([`.importlinter`](../../.importlinter)), tach ([`tach.toml`](../../tach.toml))
   and vulture run in CI, on the events in [CI events](#ci-events) (deptry too, see
   [Dependencies](#dependencies)). Cycle checks: import-linter layer contracts run on push;
   pylint `R0401` and tach run on the PR.
   ```
   Keep the trailing "See python.md… Why: enforcement.md." sentences.
3. `## Dependencies`: "PR-only CI job `deptry`" → "CI job `deptry`".

---

## Part C — `docs/repository-setup/github.md` (CI template, ~line 572)

### WHAT
1. First line inside the ```` ```yaml ```` block, above `name: CI`:
   ```yaml
   # Simplified template. mcp-coder's own .github/workflows/ci.yml splits checks by event (push vs PR).
   ```
2. Move `{name: "import-linter", cmd: "lint-imports"}` and
   `{name: "vulture", cmd: "vulture src tests --min-confidence 60"}` from the `architecture`
   matrix to the end of the `test` matrix. `architecture` keeps `tach` and `deptry` and its
   "(PR only)" comment.
3. Nothing else in `github.md` (broader refresh is #1351).

---

## Checks
- `mcp__mcp-workspace__check_file_size` passes.
- `mcp__mcp-workspace__search_files` with pattern `architecture|\btest:` in
  `.github/workflows/ci.yml` finds no job ids `test:` / `architecture:` and no comment naming them.
- pylint / mypy / pytest: not needed (no Python changed); CI runs them on the branch.

## Commit
```
ci: first-line checks on push, backup checks on PRs, full set on main
```
