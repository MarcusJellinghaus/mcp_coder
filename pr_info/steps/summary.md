# Summary — #1152 chore(ruff): add PLW1510, lint tools/, rename CI job

## Goal

Finish the ruff rollout:

1. Select `PLW1510` (`subprocess.run` without explicit `check=`) by exact code.
2. Extend ruff to `tools/` (`ruff check src tests tools`) and fix all findings except `DOC201`.
3. Rename the CI job `ruff-docstrings` → `ruff`; update helper scripts and docs to say "lint", not "docstrings".

Already done elsewhere (do NOT redo): `preview`/`explicit-preview-rules`, `SIM`, `B`, `C4`, `F`, `UP`; `TRY` rejected.

## Architectural / design changes

No runtime architecture changes — `src/` is untouched. Changes are to lint policy and CI wiring:

- **Lint scope widens** from `src tests` to `src tests tools` (CI matrix + `tools/ruff_check.sh/.bat`).
- **Rule set:** `PLW1510` added as a single code. The `PL` prefix is deliberately NOT used —
  it would re-enable pylint's disabled R category (`PLR0911/0912/0913/0915`).
- **Policy for `tools/`:** treated as low-priority scripts (may move to an MCP server or be deleted).
  - `"tools/**" = ["DOC201"]` per-file ignore.
  - `"tools/safe_delete_folder.py" = ["S607"]` per-file ignore (calls `handle.exe`/`cmd` by name on purpose).
  - Targeted `# noqa: S314` on `tools/ci_coverage_summary.py` (parses the CI's own trusted `coverage.xml`).
  - All other findings fixed in code.
- **CI check name** changes from `ruff-docstrings` to `ruff` (derived from the matrix `name`).
  Follow-up after merge: if `ruff-docstrings` is a required check on `main`, switch branch
  protection to require `ruff`. Mention this in the PR description.
- black/isort/pylint/mypy remain scoped to `src tests` (adding `tools/` there is out of scope).

## Commit / step layout (one commit per step, each green)

| Step | Commit | Content |
|---|---|---|
| 1 | `style(tools): format files touched by ruff fixes` | black + isort on `tools/` (8 files change) |
| 2 | `chore(ruff): select PLW1510, add tools/ ignores` | `pyproject.toml` only |
| 3 | `fix(tools): remove dead code flagged by ruff F` | `F541`, `F401`, `F841` |
| 4 | `chore(tools): fix remaining ruff findings` | `UP` autofix + `D`, `ANN`, `SIM`, `S314`, `B007`, `PLW1510` |
| 5 | `ci(ruff): lint tools/, rename job to ruff` | `ci.yml`, `ruff_check.sh/.bat`, `python.md` |

Ordering rationale: CI only starts linting `tools/` in step 5, after the findings are fixed, so every
commit passes CI. The `F` fixes are separate from the `UP` churn, and formatting comes before
any lint fix, as the issue requires.

## Testing approach

No new unit tests (per the issue). The "test" for each step is the ruff run on `tools/`, plus the
existing unit tests. `tests/tools/` loads `ci_coverage_summary.py`, `tach_docs.py` and the
`mlflow/*` analysers by file path, so the full fast unit test suite must stay green after
steps 1, 3 and 4.

Local tool notes:
- `run_ruff_check` / `run_ruff_fix` auto-detect only `src`/`tests` → pass
  `target_directories=["src", "tests", "tools"]` (or `["tools"]`).
- `run_format_code` → pass `target_directories=["tools"]`.
- Locally, isort cannot read 3 files with non-ASCII characters (`tools/mlflow/analyze_bash_commands.py`,
  `inspect_mlflow_run.py`, `_source_transcripts.py`; Windows `charmap` codec). Accept this —
  black still formats them, and isort on `tools/` is not in CI.

## Files modified

| File | Step | Change |
|---|---|---|
| `tools/safe_delete_folder.py` | 1, 3, 4 | format; `F541`; `D301`/`D212`/`SIM108` |
| `tools/test_scroll.py` | 1, 4 | format; `D101`/`D102` docstrings |
| `tools/tach_docs.py` | 1, 3/4 | format; `check=False`; `main() -> int`; misc |
| `tools/test_profiler_plugin/__init__.py` | 1, 3, 4 | format; bare `yield`; pytest hook annotations |
| `tools/test_profiler_plugin/generate_report.py` | 1, 4 | format; `main() -> int`; misc |
| `tools/mlflow/analyze_bash_commands.py` | 1, 4 | format; `UP`, `D301`, `D403` |
| `tools/mlflow/_source_transcripts.py` | 1, 4 | format; `UP` |
| `tools/mlflow/extract_permission_events.py` | 1, 4 | format; `UP` |
| `tools/ci_coverage_summary.py` | 4 | `UP`; `# noqa: S314` |
| `tools/mlflow/get_recent_mlflow_runs.py` | 4 | `main() -> int`; misc |
| other `tools/**/*.py` with findings | 3, 4 | autofix (`F`, `UP`, `D`) |
| `pyproject.toml` | 2 | `PLW1510` in `select`; two per-file ignores |
| `.github/workflows/ci.yml` | 5 | matrix entry renamed to `ruff`; command adds `tools` |
| `tools/ruff_check.sh`, `tools/ruff_check.bat` | 5 | header comment, echo text, command |
| `docs/repository-setup/python.md` | 5 | line 208 description |

No files are created or deleted, apart from the `pr_info/steps/` plan files.
