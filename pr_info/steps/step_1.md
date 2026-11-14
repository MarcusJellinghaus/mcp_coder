# Step 1 — Windows templates run `mcp-coder setup` (builder, test template, unit tests, docs)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Work test-first: write the unit tests below, see them fail, then change
> `command_templates.py` and the docs. Do not touch the Linux templates.
> Run pylint, pytest (fast unit set, `-n auto`), mypy and lint-imports; all must pass.
> Run the formatter, then make exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- `tests/cli/commands/coordinator/test_command_templates_setup.py`
- `tests/cli/commands/coordinator/test_command_templates.py`
- `docs/configuration/setup.md`, `docs/architecture/architecture.md`, `docs/configuration/config.md`, `docs/migration/multi-language.md`, `docs/environments/environments.md`

## Tests first — `test_command_templates_setup.py`

- Module docstring: `"""Tests for the ``mcp-coder setup`` step in the workflow and test templates."""`
- Add constants (raw strings — a lost `r` turns `\r` into a carriage return):

  ```python
  WIN_SETUP_LINE = r"mcp-coder setup --project-dir %WORKSPACE%\repo --refresh"
  WIN_CHECK_LINE = "if %ERRORLEVEL% NEQ 0 ("
  WIN_VENV_LINE = (
      r'if exist "%WORKSPACE%\repo\.venv\Scripts\python.exe" '
      r'set "VIRTUAL_ENV=%WORKSPACE%\repo\.venv"'
  )

  def _win_watchdog(failed: str, current: str, *, issue: bool = False) -> str:
      issue_part = " --issue {issue_number}" if issue else ""
      return (
          f"mcp-coder gh-tool set-status {failed} --from-status {current}{issue_part} "
          r"--project-dir %WORKSPACE%\repo --force"
      )
  ```

- `WIN_CASES`: eight `pytest.param(template, anchor, watchdog, id=...)`:
  - anchor = prefix of the line setup must precede: `"mcp-coder --log-level {log_level} <command> "` for workflows (create-plan: `"mcp-coder --log-level {log_level} create-plan {issue_number} "`), `"echo %VIRTUAL_ENV%"` for `DEFAULT_TEST_COMMAND_WINDOWS`;
  - watchdog = `_win_watchdog(...)` with the labels below, `None` for the test template.

  | template | failed | current |
  |---|---|---|
  | `CREATE_PLAN_COMMAND_WINDOWS` (`issue=True`) | `status-03f:planning-failed` | `status-03:planning` |
  | `IMPLEMENT_COMMAND_WINDOWS` | `status-06f:implementing-failed` | `status-06:implementing` |
  | `CREATE_PR_COMMAND_WINDOWS` | `status-09f:pr-creating-failed` | `status-09:pr-creating` |
  | `REVIEW_PLAN_COMMAND_WINDOWS` | `status-14f:plan-review-failed` | `status-14i:plan-reviewing` |
  | `REVIEW_IMPLEMENTATION_COMMAND_WINDOWS` | `status-17f:code-review-failed` | `status-17i:code-reviewing` |
  | `FIX_CI_COMMAND_WINDOWS` | `status-83:ci-fix-failed` | `status-82:fixing-ci` |
  | `FIX_CONFLICT_COMMAND_WINDOWS` | `status-73:merge-conflict-failed` | `status-72:fixing-merge-conflict` |

- `@pytest.mark.parametrize("template,anchor,watchdog", WIN_CASES) class TestWindowsSetupTemplates`. Work on `lines = [line.strip() for line in template.splitlines()]`; `anchor_index` = first index whose line starts with `anchor`.
  - `test_no_activate_bat`: `"activate.bat" not in template`.
  - `test_setup_before_anchor`: `lines.index(WIN_SETUP_LINE) < anchor_index`.
  - `test_failure_block`: the lines right after `WIN_SETUP_LINE` equal `[WIN_CHECK_LINE, *([watchdog] if watchdog else []), "exit /b 1", ")"]`.
  - `test_watchdog_count`: workflows → `lines.count(watchdog) == 2`; test template → `"gh-tool set-status" not in template`.
  - `test_virtual_env_between_setup_and_anchor`: `lines.index(WIN_SETUP_LINE) < lines.index(WIN_VENV_LINE) < anchor_index`.
- `test_windows_test_template_formats_with_log_level_only`: `DEFAULT_TEST_COMMAND_WINDOWS.format(log_level="INFO")` leaves no `\{[a-zA-Z_]\w*\}` match.
- `test_fix_conflict_does_not_list_plan_sessions`: also assert `r".mcp-coder\create_plan_sessions" not in FIX_CONFLICT_COMMAND_WINDOWS`.
- `test_other_templates_do_not_run_setup`: parametrize over `CREATE_PLAN_COMMAND_TEMPLATE`, `CREATE_PR_COMMAND_TEMPLATE`, `REVIEW_PLAN_COMMAND_TEMPLATE`, `DEFAULT_TEST_COMMAND` only; docstring "Linux planning/PR and test templates skip setup."

`test_command_templates.py`: delete `TestImplementTemplateProjectVenv.test_windows_template_unchanged` (superseded). Keep its other tests and imports that remain used.

## WHAT — `command_templates.py`

```python
def _windows_template(
    command: str,
    failed: str,
    current: str,
    *,
    issue_flag: bool = False,
    archive_plan_sessions: bool = True,
) -> str:
    """Return the Windows template for a workflow.

    `mcp-coder setup` runs before the command; on failure the watchdog moves the
    issue to its failed label and the script exits 1. VIRTUAL_ENV is set only
    when the project venv has an interpreter. Block bodies are not indented and
    use a literal `exit /b 1` (%ERRORLEVEL% would expand when the block is parsed).
    """
```

## HOW

- Build the text with one `rf"""…"""` string, copied from the current Windows literals. Literal braces are doubled (`{{log_level}}`); `{command}`, `{watchdog}`, `{plan_sessions}` are interpolated. Interpolated values are not re-parsed, so `command="create-plan {issue_number}"` and the watchdog's `--issue {issue_number}` keep single braces.
- The watchdog is a local variable, used twice:

  ```python
  issue = " --issue {issue_number}" if issue_flag else ""
  watchdog = (
      f"mcp-coder gh-tool set-status {failed} --from-status {current}{issue} "
      r"--project-dir %WORKSPACE%\repo --force"
  )
  plan_sessions = (
      r"dir .mcp-coder\create_plan_sessions" + "\n" if archive_plan_sessions else ""
  )
  ```

- Template body (replace the activation block; everything else as today):

  ```text
  @echo ON

  echo current WORKSPACE directory===================================
  cd %WORKSPACE%

  echo switch to python execution environment =====================
  cd %VENV_BASE_DIR%

  echo python environment ================================
  if "%VENV_BASE_DIR%"=="" (
      echo ERROR: VENV_BASE_DIR environment variable not set
      exit /b 1
  )

  mcp-coder setup --project-dir %WORKSPACE%\repo --refresh
  if %ERRORLEVEL% NEQ 0 (
  {watchdog}
  exit /b 1
  )
  if exist "%WORKSPACE%\repo\.venv\Scripts\python.exe" set "VIRTUAL_ENV=%WORKSPACE%\repo\.venv"

  set DISABLE_AUTOUPDATER=1
  set MCP_TIMEOUT=30000

  echo command execution  =====================================
  mcp-coder --log-level {{log_level}} {command} --project-dir %WORKSPACE%\repo --mcp-config .mcp.json
  set RC=%ERRORLEVEL%
  echo RC=%RC%

  {watchdog}

  echo archive after execution =======================================
  {plan_sessions}dir logs

  exit /b %RC%
  ```

- Replace the seven literals (same names, so `WORKFLOW_TEMPLATES` and `__init__` exports are unchanged):

  ```python
  CREATE_PLAN_COMMAND_WINDOWS: str = _windows_template(
      "create-plan {issue_number}", "status-03f:planning-failed", "status-03:planning",
      issue_flag=True,
  )
  IMPLEMENT_COMMAND_WINDOWS: str = _windows_template("implement", ...labels from the table...)
  # create-pr, review-plan, review-implementation, fix-ci likewise
  FIX_CONFLICT_COMMAND_WINDOWS: str = _windows_template(
      "fix-conflict", "status-73:merge-conflict-failed",
      "status-72:fixing-merge-conflict", archive_plan_sessions=False,
  )
  ```

- `DEFAULT_TEST_COMMAND_WINDOWS` (stays a raw literal): replace the 4-line `if "%VIRTUAL_ENV%"=="" ( … activate.bat )` block with

  ```text
  mcp-coder setup --project-dir %WORKSPACE%\repo --refresh
  if %ERRORLEVEL% NEQ 0 (
  exit /b 1
  )
  if exist "%WORKSPACE%\repo\.venv\Scripts\python.exe" set "VIRTUAL_ENV=%WORKSPACE%\repo\.venv"
  ```

  It sits after the `VENV_BASE_DIR` check and before `echo %VIRTUAL_ENV%`.
- Update the comment above the Windows templates: they are built by `_windows_template` and run `mcp-coder setup` before the command.

## ALGORITHM

```text
issue = " --issue {issue_number}" if issue_flag else ""
watchdog = set-status line with failed/current/issue, project dir %WORKSPACE%\repo
plan_sessions = "dir .mcp-coder\create_plan_sessions\n" or ""
return rf-template: header + VENV_BASE_DIR check + setup block(watchdog)
       + VIRTUAL_ENV line + command(command) + watchdog + archive(plan_sessions) + exit /b %RC%
```

## DATA

`_windows_template` returns a `str.format` template using `{log_level}`, plus `{issue_number}` only for create-plan. No `{branch_name}`.

## Docs

- `docs/configuration/setup.md` (~line 19), replace the Windows bullet with:
  "- Windows Jenkins templates (all workflows and the coordinator test): `--refresh`, before the workflow command. A workflow's failure moves the issue to its failed label and stops the run."
- `docs/architecture/architecture.md` (~line 130), replace the sentence "Templates for workflows that run checks and tests first run `mcp-coder setup` on the checkout (Windows executors provision through AutoRunner instead)." with "Templates first run `mcp-coder setup` on the checkout: on Linux for workflows that run checks and tests, on Windows for every workflow."
- `docs/configuration/config.md` (~line 956): "The Linux test template does not run `mcp-coder setup`; the Windows test template does. The Linux implement, fix-ci, fix-conflict and review-implementation templates and all seven Windows workflow templates run it ([Project setup](setup.md))."
- `docs/migration/multi-language.md`:
  - line ~26: "The session launcher, the Linux implement, fix-ci, fix-conflict and review-implementation templates, and all Windows templates run `mcp-coder setup`." (rest of the bullet unchanged);
  - new bullet after it: "- **Windows Jenkins runs setup in the templates (#1426).** Every Windows workflow and the coordinator test run `mcp-coder setup --refresh` instead of AutoRunner's provisioning; a workflow's setup failure moves the issue to its failed label. The changed-files check now applies on Windows too, including an untracked `uv.lock`."
  - line ~29: "Sessions and the Linux and Windows templates set it only when …".
- `docs/environments/environments.md` (~lines 119-125), replace the paragraph with:
  "**The trap this removes.** The Windows Jenkins command templates run `cd %VENV_BASE_DIR%` (eight times, in `command_templates.py`). They no longer need it for the virtualenv: they run `mcp-coder setup` and set `VIRTUAL_ENV` from absolute `%WORKSPACE%\repo` paths. Only the coordinator smoke test still needs that cwd, for its bare `claude --mcp-config .mcp.json` (see below). Before #1113, that `cd` *also* silently chose whose coding rules the agent followed, because the Claude subprocess inherited the shell's directory. Two unrelated concerns — which Python runs, and which rules apply — were coupled through one inherited variable. They are now decoupled: the rules come from `--project-dir`."

## Done when

- All new and existing template tests pass; pylint, mypy, lint-imports pass.
- `grep activate.bat` finds nothing in `command_templates.py`.
- One commit: templates + tests + docs.
