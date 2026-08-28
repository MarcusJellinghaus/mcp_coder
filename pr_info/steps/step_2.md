# Step 2 — `launch_vscode` opens the status file with the window

**Goal:** the status file tab appears exactly when a window is created or restarted — i.e.
only when a window is being raised anyway — instead of on every reload via a `folderOpen`
task.

**Context:** read [summary.md](./summary.md) first — especially the "Key design decision
(KISS)" paragraph explaining why the status path is *derived* rather than passed in.

---

## WHERE

| File | Role |
|------|------|
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | `launch_vscode` (~line 80-103) |
| `tests/workflows/vscodeclaude/test_session_launch.py` | `TestLaunch` — new test |

**No other production file changes.** In particular `session_restart.py:438`
(`launch_vscode(workspace_file)`) stays as-is, which is why the ~5 test doubles patched as
`lambda _: 9999` keep working.

## WHAT

### Test first (TDD)

Add to `TestLaunch` in `tests/workflows/vscodeclaude/test_session_launch.py`, following the
existing `test_launch_vscode_uses_code_command` pattern (it monkeypatches
`mcp_coder.workflows.vscodeclaude.session_launch.launch_process` and captures `cmd`, which
is a `str` on Windows and a `list[str]` elsewhere):

```python
def test_launch_vscode_opens_status_file(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Status file rides along with the workspace so no folderOpen task needs `code`."""
    # workspace = tmp_path / "repo_123.code-workspace"
    # expected = tmp_path / "repo_123" / ".vscodeclaude_status.txt"
    # launch_vscode(workspace)
    # cmd = captured_args[0]
    # rendered = cmd if isinstance(cmd, str) else " ".join(cmd)
    # assert str(workspace) in rendered
    # assert str(expected) in rendered
```

The existing `test_launch_vscode_*` tests keep passing unchanged (they only assert on
`"code"` and the workspace path being present).

### Implementation

```python
def launch_vscode(
    workspace_file: Path,
    session_working_dir: Path | None = None,  # pylint: disable=unused-argument
) -> int:
```

Signature and the `session_working_dir` handling are **unchanged** (it stays unused — see
summary). Inside, derive the status file and append it to both branches:

```python
    # The session folder sits beside the workspace file (see
    # workspace.get_workspace_file_path). Opening the status file here — rather than
    # from a folderOpen task — means `code` only runs when a window is being created
    # anyway; on reload VS Code restores the tab itself. See issue #1008.
    status_file = workspace_file.parent / workspace_file.stem / ".vscodeclaude_status.txt"

    if is_windows:
        return launch_process(f'code "{workspace_file}" "{status_file}"', shell=True)
    return launch_process(["code", str(workspace_file), str(status_file)])
```

Extend the docstring: note that the status file is opened alongside the workspace, and that
the path is derived from `workspace_file` (convention owned by
`workspace.get_workspace_file_path`).

## HOW (integration points)

- Callers, both unchanged:
  - `session_launch.prepare_and_launch_session:226` → `launch_vscode(workspace_file, folder_path)`
  - `session_restart.restart_closed_sessions:438` → `launch_vscode(workspace_file)`
- Both build `workspace_file` via `workspace.get_workspace_file_path(workspace_base,
  folder_name)`, so `workspace_file.parent / workspace_file.stem` is always the session
  folder. `Path.stem` strips only the final suffix, so
  `my.repo_123.code-workspace` → `my.repo_123`.
- `launch_process` signature: `(command: list[str] | str, cwd=None, shell=False, env=None,
  env_remove=None) -> int` — string form requires `shell=True` (Windows, where `code` is a
  `.cmd`).

## ALGORITHM

```
is_windows = platform.system() == "Windows"
status_file = workspace_file.parent / workspace_file.stem / ".vscodeclaude_status.txt"
if is_windows:
    return launch_process(f'code "{workspace_file}" "{status_file}"', shell=True)
else:
    return launch_process(["code", str(workspace_file), str(status_file)])
```

No `.exists()` guard: both call sites write/regenerate the status file before launching, and
a guard would add a branch plus a non-deterministic test for nothing.

## DATA

- Returns `int` — the PID from `launch_process` (unchanged contract).
- Command passed to `launch_process`: `str` on Windows (`code "<ws>" "<status>"`,
  `shell=True`), otherwise `list[str]` `["code", "<ws>", "<status>"]`.

## Definition of done

- `launch_vscode` passes `.vscodeclaude_status.txt` alongside the `.code-workspace` file on
  both platforms.
- New test passes; all pre-existing `launch_vscode` tests and the `session_restart` tests
  that patch it (`lambda _: 9999`) still pass unmodified.
- pylint, pytest (unit subset), mypy all pass; `./tools/format_all.sh` run before commit.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`, then implement step 2 only.
>
> Use MCP tools exclusively (`mcp__workspace__*` for files,
> `mcp__tools-py__run_pylint_check` / `run_pytest_check` / `run_mypy_check` for checks) as
> required by `CLAUDE.md`.
>
> Work test-first: add `test_launch_vscode_opens_status_file` to `TestLaunch` in
> `tests/workflows/vscodeclaude/test_session_launch.py`, modelled on the existing
> `test_launch_vscode_uses_code_command` (the captured command is a `str` on Windows and a
> `list[str]` elsewhere). Then edit `launch_vscode` in
> `src/mcp_coder/workflows/vscodeclaude/session_launch.py` to derive
> `workspace_file.parent / workspace_file.stem / ".vscodeclaude_status.txt"` and append it
> to both the Windows shell string and the POSIX list.
>
> Do **not** change the signature, do **not** wire up the unused `session_working_dir`
> parameter, and do **not** touch `session_restart.py` — the derivation deliberately keeps
> both call sites and their existing test doubles untouched. Do not add an `.exists()`
> guard.
>
> Then run pylint, pytest (`extra_args=["-n", "auto", "-m", "not git_integration and not
> claude_cli_integration and not claude_api_integration and not formatter_integration and
> not github_integration and not langchain_integration"]`) and mypy, fix anything they
> report, run `./tools/format_all.sh`, and make exactly one commit.
