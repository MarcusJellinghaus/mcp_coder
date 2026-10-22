# Summary — #1177: Replace bandit with ruff PLE2502, format `tools/` in CI, drop formatter scripts

## Goal

- Cover bandit `B613` (trojansource, no ruff `S` port) with ruff `PLE2502`; no bandit CI job, no bandit dependency.
- Extend the CI formatter jobs (black, isort) to `tools/`.
- Delete the redundant local formatter scripts and every doc reference to them.

## Architectural / design changes

- **Security gate:** ruff alone. `S` (from #1170) plus `PLE2502` replaces bandit. `PLE2502` is a stable rule,
  selected by exact code (not the `PL` group, which would re-enable pylint's disabled R rules), same as `PLW1510`.
  It covers `src`, `tests` and `tools`, because ruff CI already runs on all three.
- **Formatting:** one path. Local formatting goes through `mcp__mcp-tools-py__run_format_code` (formatter
  chosen by `[tool.mcp-tools-py] formatter`). The CI black/isort jobs are the backstop and now cover `tools/`,
  which `run_format_code` does not reach by default.
- **No reformat needed:** #1276 already formatted `tools/`.
- **No Python source or test code changes.** TDD does not apply: the "tests" are the existing CI/MCP checks
  (ruff with `PLE2502` must report 0 hits; black/isort check must pass on `tools`).

## Files modified

| File | Change | Step |
|---|---|---|
| `pyproject.toml` | Add `"PLE2502"` to `[tool.ruff.lint] select` with comment | 1 |
| `.github/workflows/ci.yml` | black/isort jobs: `src tests` → `src tests tools` | 2 |
| `docs/repository-setup/python.md` | Drop script mentions in Key Sections; rewrite Formatting Tools subsection to one line; move `ruff_check` row to Quality Check Tools | 2 |
| `docs/repository-setup/README.md` | Remove `tools/format_all.{sh,bat}` row | 2 |
| `docs/processes-prompts/development-process.md` | Remove `tools/format_all.bat` bullet | 2 |

## Files deleted (step 2)

- `tools/format_all.bat`
- `tools/format_all.sh`
- `tools/black.bat`
- `tools/iSort.bat`

## Files / folders created

None (apart from these `pr_info/steps/` plan files).

## Out of scope

- `docs/repository-setup/github.md:440-441` generic CI template (stays `src tests`).
- Redundant isort CLI flags `--profile=black --float-to-top` (#1174 removes the job).
- Sibling repos (propagation is separate follow-up).
- Adding `tools` to pytest `testpaths` (would collect `tools/test_*`). Don't do this.
