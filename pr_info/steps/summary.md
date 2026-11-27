# Summary — #1498 tools/: pass mypy and pylint, check it in CI, set script-directories

## Goal

`tools/` gets the same code-quality gates as `src` and `tests`: ruff (already in CI),
mypy `--strict` and pylint. Vulture, bandit, deptry, tach and lint-imports stay off
`tools/`. `[tool.mcp-tools-py] script-directories = ["tools"]` is set so that local
checks and the workflows cover the same folders as CI once MarcusJellinghaus/mcp-tools-py#308
ships. Until then the installed mcp-tools-py ignores the key.

## Architectural / design changes

- **No runtime behaviour change.** Every fix in `tools/` is a typing change, a targeted
  suppression, dead-code removal or an explicit `encoding="utf-8"`.
- **Quality-gate scope:** mypy and pylint now run on `src tests tools` everywhere they
  are pinned: CI (`ci.yml`), the upstream-compat workflow, the local `.bat` wrappers and
  the CI template in the docs. Vulture, bandit, deptry, tach, lint-imports and pytest
  scopes are unchanged.
- **Folder classification:** `pyproject.toml` declares `tools` as a *script directory*
  (`[tool.mcp-tools-py] script-directories`). This is separate from source (`where = src`)
  and tests (`testpaths = tests`). Scripts get the formatter, ruff, pylint and mypy, but not
  vulture, bandit, deptry, coverage or pytest. mcp-tools-py's fixed mapping enforces that,
  so no per-tool settings are needed.
- **Unchanged structure:** `tools/` stays a top-level package (`tools/__init__.py` is
  kept for `-p tools.test_profiler_plugin`). Scripts keep their bare sibling imports
  (`from jenkins_builds import ...`) and their `# type: ignore[import-not-found]`.
  pylint's E0401 on them is silenced per line, not by changing pylint's path.

## Constraints that shape the plan

- **Verify with explicit folders:** until #308 is installed, call `run_format_code`,
  `run_ruff_check`, `run_mypy_check` and `run_pylint_check` with
  `target_directories=["src", "tests", "tools"]` to cover `tools/`. The argument-free
  calls and the toolkit's checks don't cover it.
- **Order:** the findings are fixed (steps 1–3) before the key is set (step 5). If #308
  ships mid-way, the workflow's gates then include `tools/` only once it is clean.
- **No `assert` in `tools/`:** ruff S101 applies there.
- **mypy is platform-dependent:** CI runs it on Linux, local checks on Windows. Write
  platform guards positively (`if sys.platform == "win32":` around the body), never as an
  early return. A block that always returns takes the fallback in `else:`; otherwise
  the shared return after the block. Anything else, and one platform reports `[unreachable]`.
  `tools/safe_delete_folder.py` needed this (follow-up to step 2).
- **Pytest:** always `extra_args=["-n", "auto", ...]`. Use the fast unit-test marker
  expression from `.claude/CLAUDE.md`.

## Steps (one commit each)

| Step | Content |
|---|---|
| 1 | `jenkins_watch.py`: narrow `job` for mypy; test that `--inspect` without a job exits 2 |
| 2 | Remaining mypy findings in `tools/` (profiler report, `test_scroll.py`, mlflow scripts) |
| 3 | pylint findings in `tools/` |
| 4 | Add `tools` to the mypy / pylint command lines (CI, upstream-compat, `.bat`, docs template) |
| 5 | `script-directories = ["tools"]` in `pyproject.toml` + docs |

## Files modified (none created besides `pr_info/steps/*`)

| File | Step |
|---|---|
| `tools/jenkins_watch.py` | 1 |
| `tests/tools/test_jenkins_watch.py` | 1 |
| `tools/test_profiler_plugin/generate_report.py` | 2, 3 |
| `tools/test_scroll.py` | 2 |
| `tools/mlflow/get_latest_mlflow_db_entries.py` | 2 |
| `tools/mlflow/extract_mlflow_tool_calls.py` | 2 |
| `tools/mlflow/get_recent_mlflow_runs.py` | 2 |
| `tools/jenkins_download_log.py` | 3 |
| `tools/jenkins_download_logs.py` | 3 |
| `tools/safe_delete_folder.py` | 2 (platform guards), 3 |
| `tools/test_profiler_plugin/__init__.py` | 3 |
| `.github/workflows/ci.yml` | 4 |
| `.github/workflows/upstream-compat-check.yml` | 4 |
| `tools/mypy.bat` | 4 |
| `tools/pylint_check_for_errors.bat` | 4 |
| `docs/repository-setup/github.md` | 4 |
| `pyproject.toml` | 5 |
| `docs/configuration/toolkits.md` | 5 |
| `docs/repository-setup/python.md` | 5 |
| `docs/repository-setup/quality-and-security-checks.md` | 5 |

Not touched: `tools/vulture_check.sh`, `tools/deptry_check.sh`, `tach.toml`,
`.importlinter`, `[tool.setuptools.packages.find]`, `[tool.pytest.ini_options]`,
`tools/__init__.py`, `tools/mlflow/get_mlflow_config.py`.

## After merge (not part of this PR)

Once mcp-tools-py#308 is released and installed, check that `run_format_code`,
`run_ruff_check`, `run_mypy_check` and `run_pylint_check` without arguments cover
`tools/`, and that `run_vulture_check` / `run_bandit_check` don't.
