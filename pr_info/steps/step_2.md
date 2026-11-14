# Step 2 — Windows-only `cmd.exe` test of the rendered templates

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Step 1 is done: all Windows templates run `mcp-coder setup`.
> Write the new test file, run it with
> `run_pytest_check(extra_args=["-n", "auto", "tests/cli/commands/coordinator/test_command_templates_windows_cmd.py", "-v"])`
> and make sure its cases **pass, not skip**. Then run pylint, the fast pytest set, mypy and
> lint-imports; all must pass. Run the formatter, then make exactly one commit.

## Precondition

The test only runs on `sys.platform == "win32"`. If the run reports the cases as skipped (not a
Windows machine), write one line to `pr_info/.blocked.txt` and stop.

If a case fails because the template is wrong, fix `command_templates.py` in this step. If it
fails because the harness cannot observe the behaviour (e.g. `cmd /c` does not return the batch
file's `exit /b` code), write one line to `pr_info/.blocked.txt` and stop.

## WHERE

New file `tests/cli/commands/coordinator/test_command_templates_windows_cmd.py`. No marker.
Imports: `os`, `sys`, `pathlib.Path`, `pytest`, the eight `…_WINDOWS` templates from
`mcp_coder.cli.commands.coordinator`, and `CommandOptions`, `execute_subprocess` from
`mcp_coder.utils.subprocess_runner`. **Never import `subprocess`** (`subprocess_isolation`
import contract).

## WHAT

```python
pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="runs the templates through cmd.exe"
)

WORKFLOWS = [  # (template, command) — the args after "--log-level INFO"
    pytest.param(CREATE_PLAN_COMMAND_WINDOWS, "create-plan 42", id="create-plan"),
    pytest.param(IMPLEMENT_COMMAND_WINDOWS, "implement", id="implement"),
    pytest.param(CREATE_PR_COMMAND_WINDOWS, "create-pr", id="create-pr"),
    pytest.param(REVIEW_PLAN_COMMAND_WINDOWS, "review-plan", id="review-plan"),
    pytest.param(REVIEW_IMPLEMENTATION_COMMAND_WINDOWS, "review-implementation", id="review-implementation"),
    pytest.param(FIX_CI_COMMAND_WINDOWS, "fix-ci", id="fix-ci"),
    pytest.param(FIX_CONFLICT_COMMAND_WINDOWS, "fix-conflict", id="fix-conflict"),
]

def _run(tmp_path: Path, template: str, *, setup_rc: int, has_venv: bool) -> tuple[int, list[tuple[str, str]]]:
    """Run the rendered template through cmd.exe; return (exit code, stub calls as (args, venv))."""

def test_setup_succeeds(tmp_path, template, command, has_venv) -> None   # WORKFLOWS x has_venv in (True, False)
def test_setup_fails(tmp_path, template, expected_calls) -> None         # 7 workflows + DEFAULT_TEST_COMMAND_WINDOWS
```

`test_setup_fails` params: each workflow with `expected_calls=["setup", "gh-tool"]`, and
`DEFAULT_TEST_COMMAND_WINDOWS` with `expected_calls=["setup"]` (its success path calls the real
`claude`, `python` and `pip`, so it is not run).

## HOW — `_run`

- Layout under `tmp_path`: `ws/repo/` (`WORKSPACE=ws`), `venv_base/` (empty; `VENV_BASE_DIR`
  and cwd — cmd searches the cwd first, so it must not hold an `mcp-coder`), `stub/`,
  `stub.log`, `run.bat`. With `has_venv`, create an empty `ws/repo/.venv/Scripts/python.exe`.
- Stub `stub/mcp-coder.cmd`, written per run with the log path and setup exit code filled in:

  ```bat
  @echo off
  >>"<log>" echo ARGS=%*
  >>"<log>" echo VENV=%VIRTUAL_ENV%
  if "%1"=="setup" exit /b <setup_rc>
  exit /b 0
  ```

- Render `template.format(log_level="INFO", issue_number=42, branch_name="b")`, replace
  `"mcp-coder "` with `"call mcp-coder "` (a `.cmd` invoked without `call` never returns;
  production calls `mcp-coder.exe`, so the template text stays unchanged), and write it with
  CRLF line endings (`write_text(..., newline="\r\n")`).
- Run:

  ```python
  result = execute_subprocess(
      [os.environ["COMSPEC"], "/c", str(bat)],
      CommandOptions(
          cwd=str(venv_base),
          env={
              "WORKSPACE": str(workspace),
              "VENV_BASE_DIR": str(venv_base),
              "PATH": str(stub_dir) + os.pathsep + os.environ["PATH"],
          },
          env_remove=["VIRTUAL_ENV"],  # pytest usually runs in a venv; the wrapper clears it in production
          timeout_seconds=60,
      ),
  )
  ```

## ALGORITHM

```text
build tmp layout (+ python.exe if has_venv); write stub with log path and setup_rc
render template, prefix "call " to "mcp-coder ", write run.bat with CRLF
run cmd.exe /c run.bat via execute_subprocess (stub dir first on PATH, no VIRTUAL_ENV)
read stub.log lines; pair them as (ARGS=…, VENV=…) calls, strip the prefixes
return result.return_code, calls
```

## DATA / assertions

- `calls: list[tuple[str, str]]` — `(args, virtual_env)` per stub invocation, in order.
- `test_setup_succeeds` (`workspace = tmp_path / "ws"`, the same path `_run` uses):
  - `calls[0][0] == f"setup --project-dir {workspace}\\repo --refresh"`;
  - exactly one call whose args start with `f"--log-level INFO {command} "` (the workflow command is reached);
  - its `virtual_env == f"{workspace}\\repo\\.venv"` when `has_venv`, else `""`;
  - return code 0.
- `test_setup_fails`:
  - return code 1;
  - `[args.split()[0] for args, _ in calls] == expected_calls` (watchdog called for workflows, command never reached).

## Done when

- All 22 cases pass on Windows (14 success, 8 failure); pylint, mypy, lint-imports pass.
- One commit: the new test file (plus any template fix it exposed).
