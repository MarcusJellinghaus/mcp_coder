# Step 1 — Windows workflow templates run in `%WORKSPACE%\repo` and list all sessions

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Write the tests first, then change the template and the docs. Run pylint, pytest (fast
> unit set, plus `tests/cli/commands/coordinator/test_command_templates_windows_cmd.py`
> explicitly) and mypy; all must pass. Run `run_format_code`, then commit only the files
> listed under WHERE in one commit.

## Precondition

The `cmd.exe` test only runs on Windows. If `sys.platform != "win32"` in the environment
running this step, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `tests/cli/commands/coordinator/test_command_templates_setup.py`
- `tests/cli/commands/coordinator/test_command_templates_windows_cmd.py`
- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- `docs/environments/environments.md`

## WHAT

### Tests: `test_command_templates_setup.py`

Replace `test_fix_conflict_does_not_list_plan_sessions` with:

```python
WIN_WORKFLOWS = [
    pytest.param(param.values[0], id=param.id) for param in WIN_CASES if param.id != "test"
]


@pytest.mark.parametrize("template", WIN_WORKFLOWS)
def test_windows_workflow_runs_in_repo_and_lists_sessions(template: str) -> None:
    """Windows workflows run in the repo and list all of .mcp-coder and logs."""


def test_linux_fix_conflict_does_not_list_plan_sessions() -> None:
    """fix-conflict keeps its archive section without plan sessions."""
    assert ".mcp-coder/create_plan_sessions" not in FIX_CONFLICT_COMMAND_TEMPLATE
```

The Linux function keeps the old test's Linux assertion only until step 3 replaces it.

ALGORITHM (Windows test):
```
lines = _stripped_lines(template)
for line in (r"cd %WORKSPACE%\repo", "if exist .mcp-coder dir /s .mcp-coder", "dir logs"):
    assert line in lines
assert "VENV_BASE_DIR" not in template
assert "create_plan_sessions" not in template
```

### Tests: `test_command_templates_windows_cmd.py`

- `import re`.
- `_run(tmp_path, template, *, setup_rc, has_venv) -> tuple[int, list[tuple[str, str]], str]`:
  return `(result.return_code, calls, result.stdout)`.
- Rewrite with `re.sub(r"(?m)^mcp-coder ", "call mcp-coder ", script)` instead of
  `script.replace("mcp-coder ", "call mcp-coder ")`. The unanchored replace would turn
  `if exist .mcp-coder dir …` into `.call mcp-coder dir …`. All `mcp-coder` command lines
  in the templates start at column 0, since block bodies are not indented.
- Create `ws\repo\logs\repo_log_marker.txt` and `venv_base\logs\venv_log_decoy.txt`.
- Keep `cwd=str(venv_base)`: the wrapper starts there, so the template's own `cd` is what is
  under test. Replace the comment `# VENV_BASE_DIR is also the cwd: …` with:
  `# The script starts in VENV_BASE_DIR, like the Jenkins wrapper; neither it nor ws\repo holds an mcp-coder (cmd searches the cwd first).`
- `test_setup_succeeds`: unpack `return_code, calls, stdout = _run(...)`, then:
  - `assert "repo_log_marker.txt" in stdout`
  - `assert "venv_log_decoy.txt" not in stdout`

  The echoed command line `dir logs` contains neither name, so these assertions prove where the
  listing ran.
- `test_setup_fails`: unpack `return_code, calls, _ = _run(...)`.

### Implementation: `_windows_template` in `command_templates.py`

New signature (flag removed):
```python
def _windows_template(
    command: str, failed: str, current: str, *, issue_flag: bool = False
) -> str:
```

Changes to the returned `rf"""…"""` string (keep it a raw f-string):
- `cd %WORKSPACE%` → `cd %WORKSPACE%\repo` (under the existing
  `echo current WORKSPACE directory…` banner).
- Delete the `echo switch to python execution environment …` banner, `cd %VENV_BASE_DIR%`,
  and the `if "%VENV_BASE_DIR%"=="" ( … )` block. Keep the `echo python environment …` banner.
- Archive section becomes:
  ```
  echo archive after execution =======================================
  if exist .mcp-coder dir /s .mcp-coder
  dir logs
  ```
- Delete the `plan_sessions` variable.
- Docstring: add that the script runs in `%WORKSPACE%\repo` so the relative listing finds the
  project's `.mcp-coder` and `logs`, and that `if exist` guards `dir /s` (on a missing
  folder `dir /s` searches the whole tree).

Remove `archive_plan_sessions=False` from the `FIX_CONFLICT_COMMAND_WINDOWS` call.
Leave `DEFAULT_TEST_COMMAND_WINDOWS` and all Linux templates untouched.

### Docs: `docs/environments/environments.md` (lines ~120-124)

Rewrite the first sentences of "The trap this removes." along these lines: the Windows Jenkins
workflow templates run in `%WORKSPACE%\repo` and use absolute `%WORKSPACE%\repo` paths for
`mcp-coder setup` and `VIRTUAL_ENV`. Only the coordinator smoke test still runs
`cd %VENV_BASE_DIR%`, for its bare `claude --mcp-config .mcp.json` (see below). Keep the
rest of the paragraph (the #1113 history) as is. Drop "eight times".

## HOW

No new imports in production code. The test adds `import re`. No other integration points change.

## DATA

Template constants stay `str`. `_run` returns a 3-tuple:
`(return_code: int, calls: list[tuple[args, venv]], stdout: str)`.

## Done when

- The new and updated tests pass, including the `cmd.exe` test on Windows.
- `grep "cd %VENV_BASE_DIR%"` finds only `DEFAULT_TEST_COMMAND_WINDOWS` in `command_templates.py`.
- pylint, mypy and pytest pass.
