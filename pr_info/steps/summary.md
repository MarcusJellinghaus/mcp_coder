# Summary — #1488: Windows workflow templates run in the repo, list all sessions, print tool versions

## Goal

Fix three defects in the Jenkins workflow command templates
(`src/mcp_coder/cli/commands/coordinator/command_templates.py`):

1. Windows workflow templates `cd %VENV_BASE_DIR%` (the tool env), so the relative archive
   listing (`dir .mcp-coder\create_plan_sessions`, `dir logs`) lists the tool env instead of
   `%WORKSPACE%\repo`, where mcp-coder writes them.
2. Every workflow except fix-conflict lists only `.mcp-coder/create_plan_sessions`, which only
   create-plan writes. Other workflows write other session folders.
3. Windows workflow logs do not show which Claude Code / mcp-coder ran.

## Architectural / design changes

- **Working directory of the Windows workflow templates.** `_windows_template` now changes to
  `%WORKSPACE%\repo` (was `%VENV_BASE_DIR%`). The Windows and Linux workflow templates now run
  with the same cwd: the checkout. Nothing in the workflow templates relied on the tool env as
  cwd (`--mcp-config .mcp.json` resolves against `--project-dir`; `setup`/`gh-tool` take
  `--project-dir`; `mcp-coder` comes from `PATH`). The workflow templates no longer reference
  `%VENV_BASE_DIR%` at all, so its banner and empty-check are removed from them.
- **The smoke-test templates are unchanged.** `DEFAULT_TEST_COMMAND` and
  `DEFAULT_TEST_COMMAND_WINDOWS` keep their `cd %VENV_BASE_DIR%`. Their `prompt` calls without
  `--project-dir` write logs into the tool env, and their bare `claude --mcp-config .mcp.json`
  needs the tool env's `.mcp.json`. The smoke test is now the only template that does this `cd`.
- **One uniform archive section.** The per-builder `archive_plan_sessions` flag is removed from
  `_windows_template` and `_linux_setup_template`. Every workflow template lists the whole
  `.mcp-coder` tree recursively, plus `logs`, so each workflow shows its own session folder
  (`implement_sessions`, `review_plan_sessions`, `rebase_sessions`, …) without per-workflow
  configuration:
  - Windows: `if exist .mcp-coder dir /s .mcp-coder` (a bare `dir /s` on a missing folder
    searches the whole repo) and `dir logs`.
  - Linux: `ls -laR .mcp-coder || true` and `ls -la logs || true` (the executor runs under
    `set -e`; a missing folder must not abort before `exit $RC`).
- **Tool versions in Windows logs.** `_windows_template` prints `where claude.exe`,
  `call claude.exe --version`, `where mcp-coder` and `call mcp-coder --version`, after
  `set MCP_TIMEOUT=…` and before the command, which matches the Linux templates. `claude.exe` (not `claude`)
  is used because, with the repo as cwd, cmd.exe searches the cwd first and repos such as this
  one have a root `claude.bat` launcher. `call` keeps a `.cmd` from ending the batch; the `call`
  lines contain no `%` (`call` expands `%` twice, #1426).
- **Exit code unchanged.** `RC` is still captured right after the command, so a failing `dir`,
  `ls`, `where` or `--version` line cannot change the result.

## Constraints that apply to every step

- Windows template strings stay raw strings (`r"""` / `rf"""`): `%WORKSPACE%\repo` contains
  `\r`.
- Paths stay unquoted, like the existing setup line. `cd %WORKSPACE%\repo` has no `/d`.
- Do not change `DEFAULT_TEST_COMMAND` or `DEFAULT_TEST_COMMAND_WINDOWS`.
- Code comments/docstrings say what the code does and why, not which issue changed it.
- The `cmd.exe` test (`test_command_templates_windows_cmd.py`) is skipped off Windows and CI has
  no Windows job: run it on Windows before committing each Windows step.

## Files modified

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | `_windows_template`: cwd, archive, version lines, flag removed. `_linux_setup_template` + `CREATE_PR_COMMAND_TEMPLATE`: archive, flag removed. Fix-conflict calls drop `archive_plan_sessions=False`. |
| `tests/cli/commands/coordinator/test_command_templates_setup.py` | `test_fix_conflict_does_not_list_plan_sessions` replaced by parametrised Windows and Linux workflow-template tests. |
| `tests/cli/commands/coordinator/test_command_templates_windows_cmd.py` | Anchored `mcp-coder` rewrite, `_run` returns stdout, `logs` marker/decoy, `claude` stub/decoy, cwd comment. |
| `docs/environments/environments.md` | "eight times" paragraph: only the smoke test still runs `cd %VENV_BASE_DIR%`. |

No files or modules are created (apart from these `pr_info/steps/` files).

## Steps

1. `step_1.md`: Windows workflow templates run in `%WORKSPACE%\repo` and list all sessions (plus docs).
2. `step_2.md`: Windows workflow templates print the Claude Code and mcp-coder versions.
3. `step_3.md`: Linux workflow templates list all sessions.

## After merge (not checkable in this PR)

The change reaches Jenkins only after Rebuild-mcp-coder-dev. A real Windows run must confirm:
- create-plan lists the new files under `.mcp-coder\create_plan_sessions`;
- `logs` shows current files;
- `where claude.exe` / `--version` print, and the command still runs.

A Linux log must confirm the cwd is the checkout. AutoRunner's `run-mcp-command.bat` now carries
on in `%WORKSPACE%\repo` after the `call`.

Known residual risk, out of scope: with the repo as cwd, a driven repo with a root
`mcp-coder.bat`/`.cmd` would shadow the `mcp-coder` on `PATH`. This repo has none.
