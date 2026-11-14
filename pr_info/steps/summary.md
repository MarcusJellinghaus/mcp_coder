# Summary — #1426: Windows command templates run `mcp-coder setup` and set `VIRTUAL_ENV`

## Goal

Windows Jenkins sets up the project the way Linux does (#1204):

- every Windows template runs the repo's declared setup (`mcp-coder setup --refresh`) before its command;
- a workflow whose setup fails runs its watchdog (issue moves to its failed label) and exits 1;
- `VIRTUAL_ENV` is set only when `repo\.venv\Scripts\python.exe` exists, so a repo without a `.venv` (e.g. npm) still runs every workflow.

Companion of MarcusJellinghaus/AutoRunner#59, which makes the project venv optional in `run-mcp-command.bat`.

## Architectural / design changes

- **Setup moves from AutoRunner into the templates on Windows.** Before: AutoRunner's Executor provisioned `repo\.venv` before the COMMAND, so a setup failure never reached the watchdog inside the COMMAND. After: the COMMAND runs `mcp-coder setup` itself, so the watchdog covers setup failures. Future setup changes land in mcp-coder alone.
- **No more `activate.bat`.** The `if "%VIRTUAL_ENV%"=="" ( …activate.bat )` block is removed from all eight Windows templates. It would never return without `call` once the project venv is optional, and it pointed `VIRTUAL_ENV` at the tool env.
- **One builder for the seven Windows workflow templates.** `_windows_template(command, failed, current, *, issue_flag=False, archive_plan_sessions=True)` replaces seven near-identical raw-string literals. It mirrors `_linux_setup_template`. The Linux templates and `_watchdog` are unchanged; no shared Linux/Windows label table.
- **The Windows smoke test (`DEFAULT_TEST_COMMAND_WINDOWS`) runs setup too**, without a watchdog (it has no issue): on failure it runs `exit /b 1`. It stays a raw literal with the setup lines inline.
- **Batch shape of the new block** (no indentation inside the block; literal `exit /b 1`; `if %ERRORLEVEL% NEQ 0 (` rather than `if errorlevel 1`, so negative NTSTATUS codes count as failure):

  ```bat
  mcp-coder setup --project-dir %WORKSPACE%\repo --refresh
  if %ERRORLEVEL% NEQ 0 (
  <watchdog line — workflows only>
  exit /b 1
  )
  if exist "%WORKSPACE%\repo\.venv\Scripts\python.exe" set "VIRTUAL_ENV=%WORKSPACE%\repo\.venv"
  ```

- **Verification:** exact-line unit tests (run everywhere) plus a Windows-only test that runs each rendered template through `cmd.exe` with a stub `mcp-coder.cmd`. mcp-coder's CI has no Windows job, so the `cmd.exe` test runs on Windows dev machines only.

Unchanged: the `cd %VENV_BASE_DIR%` / `VENV_BASE_DIR` check, the relative `--mcp-config .mcp.json`, the Linux templates, the `mcp-tools-py` probes (#1199), `WORKFLOW_TEMPLATES`, placeholders (`{log_level}` everywhere, `{issue_number}` only in create-plan, no `{branch_name}` on Windows).

## Files

| File | Change | Step |
|---|---|---|
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | add `_windows_template`; rebuild the seven `…_COMMAND_WINDOWS` with it; edit `DEFAULT_TEST_COMMAND_WINDOWS` | 1 |
| `tests/cli/commands/coordinator/test_command_templates_setup.py` | fix module docstring; add Windows exact-line tests; update `test_other_templates_do_not_run_setup` and the fix-conflict archive test | 1 |
| `tests/cli/commands/coordinator/test_command_templates.py` | delete `test_windows_template_unchanged` | 1 |
| `docs/configuration/setup.md` | Windows bullet (~line 19) | 1 |
| `docs/architecture/architecture.md` | reword ~line 130 | 1 |
| `docs/configuration/config.md` | split ~line 956 by OS | 1 |
| `docs/migration/multi-language.md` | lines ~26 and ~29, new Windows bullet | 1 |
| `docs/environments/environments.md` | rewrite the `cd %VENV_BASE_DIR%` rationale (~lines 119-125) | 1 |
| `tests/cli/commands/coordinator/test_command_templates_windows_cmd.py` | **new**: Windows-only `cmd.exe` test | 2 |

No new modules in `src/`, no `.importlinter` changes (the new test uses `execute_subprocess` from `mcp_coder.utils.subprocess_runner`, never `subprocess`).

## Steps

1. [step_1.md](./step_1.md) — Windows templates run setup: builder, test template, unit tests, docs.
2. [step_2.md](./step_2.md) — Windows-only `cmd.exe` test of the rendered templates.
