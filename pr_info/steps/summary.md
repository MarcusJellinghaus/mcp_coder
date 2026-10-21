# Summary: Import-health check (#1246)

## Goal

Prove at test time that **every** `mcp_coder` module imports — including lazy
modules (langchain backends, `icoder`, `copilot_cli`, workflows) that a CLI run
never loads. Run the same check against upstream `main` in the upstream CI
workflow, so a stale/renamed upstream name, a removed upstream submodule, or an
import-time error in an upstream package is caught early (root cause class of #1243).

## Architectural / design changes

- **Test-only change.** Nothing in `src/` changes. No CLI flag, no `__init__` diagnostic.
- **Subprocess isolation.** The walk runs in a fresh interpreter
  (`sys.executable -P tests/_import_walker.py <report.json>`) launched via
  `mcp_coder.utils.subprocess_runner.execute_subprocess`. Reason:
  `tests/llm/providers/langchain/conftest.py` injects `MagicMock`s into
  `sys.modules`; an in-process walk could pass against mocks.
  - `PYTHONPATH` = parent dir of the test process's `mcp_coder.__file__`.
  - `-P` keeps `tests/` (the script dir) off `sys.path`, so `tests/utils`,
    `tests/llm`, … cannot shadow real packages.
  - Results go to a JSON file, not stdout (modules may print at import).
- **Walker = non-collected helper module** `tests/_import_walker.py`
  (stdlib-only, linted and type-checked like other test code; precedent:
  `tests/langchain_doubles.py`).
- **Custom recursive walk** (`pkgutil.iter_modules` + `importlib.import_module`),
  not `pkgutil.walk_packages` (which hides failed subpackages and drops the
  exception). A failing package is reported once; its subtree is not walked.
  `mcp_coder.__main__` is skipped (raises `SystemExit`).
- **Classification** — one function `missing_optional_package(exc)`:
  first `ModuleNotFoundError` in the `__cause__`/`__context__` chain whose
  top-level package is not importable → **skip** (optional extra absent);
  everything else → **fail**.
- **Strict mode:** env var `MCP_CODER_IMPORT_TEST_STRICT=1` turns skips into failures.
- **Root import failure** (e.g. `_depcheck` → `SystemExit(1)`) simply crashes
  the walker; the test asserts `return_code == 0` and shows stderr.
- **Single test, no marker** — runs in the normal unit-test job; one ~10 s
  subprocess walk regardless of xdist worker count.
- **Upstream CI** (`.github/workflows/upstream-mypy-check.yml`): job renamed to
  `upstream-compat` / `upstream-compat-*`; installs `.[typecheck,test,langchain]`
  after the upstream git installs; runs mypy and the import test (strict) as
  independent steps — neither masks the other.

## Files

| Action | Path | Purpose |
|---|---|---|
| Create | `tests/_import_walker.py` | Stdlib-only walker + `missing_optional_package` classifier; script entry writes JSON report |
| Create | `tests/test_module_imports.py` | Classification unit tests + the subprocess import-health test |
| Modify | `.github/workflows/upstream-mypy-check.yml` | Rename job, wider install extras, independent mypy + import-test steps |

No `src/` changes, no new packages/folders, no docs references to update
(the old job name appears only in the workflow file).

## Steps

1. `step_1.md` — walker + classification tests + import-health test (one commit).
2. `step_2.md` — upstream CI workflow changes (one commit).
