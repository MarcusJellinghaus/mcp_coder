# Step 2 — Windows workflow templates print the Claude Code and mcp-coder versions

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly
> (step 1 is already committed). Write the tests first, then change `_windows_template`.
> Run pylint, pytest (fast unit set, plus
> `tests/cli/commands/coordinator/test_command_templates_windows_cmd.py` explicitly) and mypy;
> all must pass. Run `run_format_code`, then commit only the files listed under WHERE in one
> commit.

## Precondition

The `cmd.exe` test only runs on Windows. If `sys.platform != "win32"` in the environment
running this step, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `tests/cli/commands/coordinator/test_command_templates_setup.py`
- `tests/cli/commands/coordinator/test_command_templates_windows_cmd.py`
- `src/mcp_coder/cli/commands/coordinator/command_templates.py`

## WHAT

### Tests: `test_command_templates_setup.py`

Add, reusing `WIN_WORKFLOWS` from step 1:

```python
WIN_VERSION_LINES = (
    "where claude.exe",
    "call claude.exe --version",
    "where mcp-coder",
    "call mcp-coder --version",
)


@pytest.mark.parametrize("template", WIN_WORKFLOWS)
def test_windows_workflow_prints_tool_versions(template: str) -> None:
    """Windows workflows print Claude Code and mcp-coder versions before the command."""
```

ALGORITHM:
```
lines = _stripped_lines(template)
command_index = _anchor_index(lines, "mcp-coder --log-level ")
timeout_index = lines.index("set MCP_TIMEOUT=30000")
for line in WIN_VERSION_LINES:
    assert timeout_index < lines.index(line) < command_index
```

Checking the exact `call` lines also proves they contain no `%`.

### Tests: `test_command_templates_windows_cmd.py`

- In `_run`:
  - Write `stub_dir / "claude.cmd"` containing `@echo off` / `echo CLAUDE_STUB %*`, with
    `newline="\r\n"`. It writes only to stdout, never to the stub log: the log parser reads
    `ARGS`/`VENV` lines in pairs.
  - Write the decoy `ws\repo\claude.bat` containing `@echo off` / `echo CLAUDE_DECOY`.
  - After the anchored `mcp-coder` rewrite, apply `.replace("claude.exe", "claude.cmd")`.
    Comment: the test cannot create a real `claude.exe`. An explicit extension still
    skips the repo's `claude.bat`, so the stub is found via `PATH`.
- In `test_setup_succeeds`, add:
  - `assert "CLAUDE_STUB --version" in stdout`
  - `assert "CLAUDE_DECOY" not in stdout`
  - `assert ("--version" in [args for args, _ in calls])`, the `call mcp-coder --version` line.

Existing assertions still hold. `calls[0]` is still `setup`, because the version lines come
after it. In `test_setup_fails`, the script exits before the version lines.

### Implementation: `_windows_template` in `command_templates.py`

Between `set MCP_TIMEOUT=30000` (plus its blank line) and `echo command execution …`, insert:

```
echo tool versions =====================================
where claude.exe
call claude.exe --version
where mcp-coder
call mcp-coder --version

```

Extend the docstring by one sentence. It uses `claude.exe` because cmd searches the cwd (the
repo, which may hold a `claude.bat` launcher) before `PATH`. `call` keeps a `.cmd` from ending
the batch, and the `call` lines contain no `%` because `call` expands it a second time.

Leave `DEFAULT_TEST_COMMAND_WINDOWS` untouched.

## HOW

No new imports. No integration changes: `RC` is still captured right after the command, so the
version lines cannot change the exit code.

## DATA

No signature or return-type changes.

## Done when

- The new tests and the `cmd.exe` test pass on Windows.
- pylint, mypy and pytest pass.
