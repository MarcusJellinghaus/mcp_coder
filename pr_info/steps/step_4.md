# Step 4 — add `tools` to the mypy and pylint command lines

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`), then implement
> step 4 only. Command-line and docs-template edits; no Python code. Run the checks below and
> commit (one commit).

## Tests

None. CI runs these commands. Steps 2 and 3 made `src tests tools` pass mypy and pylint,
which is what these command lines now check.

## WHERE / WHAT

| File | Current | New |
|---|---|---|
| `.github/workflows/ci.yml` (~line 183) | `mypy --version && mypy --strict src tests` | `mypy --version && mypy --strict src tests tools` |
| `.github/workflows/ci.yml` (~line 231) | `pylint --version && pylint ./src ./tests` | `pylint --version && pylint ./src ./tests ./tools` |
| `.github/workflows/upstream-compat-check.yml` (~line 54) | `run: mypy --strict src tests` | `run: mypy --strict src tests tools` |
| `tools/mypy.bat` | `... --strict-optional src tests` | `... --strict-optional src tests tools` |
| `tools/pylint_check_for_errors.bat` | `pylint -E  ./src ./tests` | `pylint -E ./src ./tests ./tools` |
| `docs/repository-setup/github.md` (~line 618) | `pylint -E ./src ./tests` | `pylint -E ./src ./tests ./tools` |
| `docs/repository-setup/github.md` (~line 620) | `mypy --strict src tests` | `mypy --strict src tests tools` |

## HOW

- Edit only the commands named above. In the template, keep `-E` on pylint and the vulture
  line at `src tests`.
- Don't touch `tools/vulture_check.sh`, `tools/deptry_check.sh`, the bandit, tach or
  lint-imports jobs, or the comment at the top of `upstream-compat-check.yml`.
- `pyproject.toml` and `.github/workflows/` are on the advisory sensitive-files list. The PR
  warning is expected.

## ALGORITHM / DATA

None.

## Checks before commit

1. `search_files(pattern="mypy --strict src tests(?! tools)|pylint (-E +)?\\./src \\./tests(?! \\./tools)")`:
   no hits in the files above (hits elsewhere, e.g. `pr_info/`, are fine)
2. `run_mypy_check(target_directories=["src", "tests", "tools"])` and
   `run_pylint_check(target_directories=["src", "tests", "tools"])`: clean (no regression)
3. Fast unit-test run from `.claude/CLAUDE.md` (with `-n auto`): pass

Commit message: `ci: run mypy and pylint on tools/`
