# Summary — Issue #1298: migrate `mcp_verification` to `execute_command`; document remaining `subprocess` exceptions

## Goal

Tighten the `subprocess_isolation` import-linter contract:

- `mcp_coder.utils.mcp_verification` stops importing `subprocess` and goes through
  `mcp_coder.utils.subprocess_runner.execute_command`.
- `tests/install` stops reaching `subprocess` / `shutil` through `_env.<module>`
  attribute access (a bypass import-linter cannot see) and gets an explicit exemption.
- Every remaining exception in the contract has a documented reason in `.importlinter`.

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| `verify_mcp_servers` `--version` call | `subprocess.run(...)`, no timeout, catches `OSError` | `execute_command(..., timeout_seconds=30)`; result mapped to `RuntimeError` in order `timed_out` → `execution_error` → non-zero `return_code` |
| `subprocess_isolation` exemptions | 5 entries, none documented, one hidden bypass (`tests.install` via `_env.subprocess`) | 4 entries, all documented, no hidden bypass |
| `tests/install` access to `subprocess` / `shutil` | via `_env.subprocess` / `_env.shutil` + `type: ignore[attr-defined]` | plain `import subprocess` / `import shutil` |

Public behaviour of `verify_mcp_servers` is unchanged: it still raises `FileNotFoundError` (missing
binary) or `RuntimeError` (version check failed). New: a hang now turns into a `RuntimeError` after
30s instead of blocking forever.

Key facts the design relies on (verified against `mcp-coder-utils` source):

- `execute_command` never raises on launch failure; it returns
  `CommandResult(return_code=1, execution_error="<Type>: <msg>")`.
- On timeout it returns `timed_out=True` **and** sets `execution_error="Process timed out after N seconds"`,
  so `timed_out` must be checked first.
- import-linter treats an unmatched `ignore_imports` entry as an error, so each `ignore_imports`
  edit lands in the same commit as its code change.

Resulting `ignore_imports` of `subprocess_isolation`:

```
mcp_coder.workflows.vscodeclaude.session_setup -> subprocess
tests.workflows.vscodeclaude.test_session_setup_flow -> subprocess
mcp_coder.install.** -> subprocess
tests.install.** -> subprocess
```

## Files modified

| File | Step | Change |
|---|---|---|
| `src/mcp_coder/utils/mcp_verification.py` | 1 | Use `execute_command`; drop `import subprocess`; update docstring `Raises` |
| `tests/utils/test_mcp_verification.py` | 1 | Patch `execute_command` with `CommandResult`; parametrized failure test; drop `subprocess` / `MagicMock` |
| `.importlinter` | 1, 2 | Step 1: remove 2 `mcp_verification` entries. Step 2: add `tests.install.** -> subprocess` + reason comment block |
| `tests/install/conftest.py` | 2 | Remove `_env` shim, its comment and the docstring "Subprocess note" |
| `tests/install/test_install_integration.py` | 2 | Plain `import subprocess`; remove "Subprocess note" |
| `tests/install/test_install_phases.py` | 2 | Plain `import subprocess` / `import shutil`; remove `_shutil` shim + comment and "Subprocess note" |

No files or folders are created (apart from these plan files). No production code outside
`mcp_verification.py` changes.

## Steps

1. `step_1.md` — Migrate `verify_mcp_servers` to `execute_command` (tests first), drop its two exemptions.
2. `step_2.md` — Remove the `tests/install` `_env` bypass, add the explicit exemption, document all remaining exceptions.

## Out of scope

- Direct `["git", ...]` calls (already go through the runner).
- An interactive / inherited-stdio runner in `mcp-coder-utils`.
- Migrating `vscodeclaude.session_setup` or `mcp_coder.install` (permanent exceptions).
