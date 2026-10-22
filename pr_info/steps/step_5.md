# Step 5 — CI: lint `tools/`, rename job to `ruff`; scripts and docs

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_5.md`). Implement only this
> step: widen the ruff command to `src tests tools`, rename the CI job to `ruff`, and update the helper scripts and
> docs.

## Precondition

`run_ruff_check(target_directories=["src", "tests", "tools"])` reports 0 findings. If it does not, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE / WHAT

1. `.github/workflows/ci.yml:~103`:
   ```yaml
   - {name: "ruff", cmd: "ruff version && ruff check src tests tools"}
   ```
2. `tools/ruff_check.sh`:
   - header `# Check docstrings using ruff (D + DOC rules)` → `# Lint src, tests and tools using ruff`
   - `echo "Checking docstrings with ruff..."` → `echo "Linting with ruff..."`
   - `ruff check src tests "$@"` → `ruff check src tests tools "$@"`
3. `tools/ruff_check.bat`: the same three changes (`REM` header, `echo`, `ruff check src tests tools %*`).
4. `docs/repository-setup/python.md:208`:
   `| \`ruff_check.sh/bat\` | Run ruff lint on src/tests/tools | Optional |`

## HOW

- `search_files(pattern="ruff-docstrings")` must return no hits afterwards, except `pr_info/` if anything there matches.
- `search_files(pattern="Check docstrings|docstring checks")` in `tools/` and `docs/` → no stale wording.

## ALGORITHM

```
check precondition
edit ci.yml matrix entry
edit ruff_check.sh / .bat (3 lines each)
edit python.md line
grep ruff-docstrings -> none
commit "ci(ruff): lint tools/, rename job to ruff"
```

## DATA

The CI check name changes from `ruff-docstrings` to `ruff`.
**PR description must include:** "After merge: if `ruff-docstrings` is a required status check on `main`,
update branch protection to require `ruff` instead."

## Checks

ruff (`src tests tools`), fast unit tests, pylint and mypy pass.
