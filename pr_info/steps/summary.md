# Summary — #1388: mcp_tools_py shim: remove dead check wrappers

## Problem

`has_mypy_errors` in `src/mcp_coder/mcp_tools_py.py` reads only `errors_found`. That field is `None` or `0` on failed runs, so a failed mypy run reads as clean. Nothing calls it any more. Since #1401 every workflow check (format, mypy, pylint, pytest) runs through the toolkit bindings (`utils/toolkit_runner.run_binding`), so all of the shim's run wrappers are dead code. We delete them instead of fixing them.

## Architectural / design changes

- **Shim narrowed to its real role.** `mcp_coder.mcp_tools_py` goes from "check runner" (mypy/pylint/pytest/format wrappers plus result re-exports) to a single re-export of `resolve_steps`. It stays the only permitted importer of the `mcp_tools_py` package (`.importlinter` contract `mcp_checker_isolation`, `tach.toml`). Its only `src/` user is `cli/commands/verify_sections.py`.
- **One path for check results.** Workflows get check results only through the toolkit (`utils/toolkit_runner`). The toolkit maps `result.error` to `status="error"`, which guarantees that a failed run never reads as clean. Callers (`_run_check`, `_run_all_checks`) already treat `status == "error"` as a failure. No parallel path through the shim remains.
- **Docs and comments match reality.** `enforcement.md` and the `tach.toml` comments stop describing the shim as the quality-tool runner.
- **No changes to dependencies or contracts.** `.importlinter` is unchanged. In `tach.toml` only comments change; every `depends_on` entry stays.

## Files modified / deleted

| File | Change | Step |
|---|---|---|
| `src/mcp_coder/mcp_tools_py.py` | Trim to the `resolve_steps` re-export | 1 |
| `tests/test_mcp_tools_py.py` | Keep only `test_resolve_steps_reexported` (module-level) | 1 |
| `tests/test_mcp_tools_py_integration.py` | **Delete** | 1 |
| `pyproject.toml` | Remove the `checker_integration` marker and its usage comment | 1 |
| `vulture_whitelist.py` | Remove the `_.has_mypy_errors` entry and its comment | 1 |
| `tach.toml` | Comment-only edits | 2 |
| `docs/architecture/enforcement.md` | Fix the quality-tool boundary sentence | 2 |
| `docs/tests/issues.md` | Remove the Issue #011 and Issue #008 entries | 2 |

No files or folders are created (apart from these plan files).

**Do not touch:** `.importlinter`, `tach.toml` `depends_on` entries, `docs/tests/runtime_statistics.md`, `docs/tests/performance_data/`, `docs/architecture/dependencies/*` (generated), `tools/tach_docs.py`.

## Steps

1. **Code:** remove the dead wrappers from the shim, along with their tests, the integration test file, the marker and the vulture entry. This is one commit because deleting the integration test file and removing its `checker_integration` marker must land together (`--strict-markers`).
2. **Docs and comments:** `tach.toml` comments, `enforcement.md`, `docs/tests/issues.md`. Independent of step 1's runtime behaviour, so it is a separate commit.

## TDD note

This is a pure removal. No new behaviour needs a failing test first. The remaining test (`test_resolve_steps_reexported`) pins the one behaviour the shim keeps, and it must pass after step 1.
