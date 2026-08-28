# Summary — Issue #1008: stop generated session files from raising background windows

## Problem

With several VSCodeClaude per-issue windows open, keyboard focus sometimes jumps from the
window being typed in to another window. The generated `.vscode/tasks.json` defines two
`runOn: folderOpen` tasks that fire on every window **open and reload** without a prompt
(`task.allowAutomaticTasks: "on"` in `WORKSPACE_FILE_TEMPLATE`):

1. **"Open Status File" shells out to `code`** — `code <file>` does not spawn a process; it
   hands the path to the running VS Code instance over IPC and that instance **raises and
   focuses** the target window. `"reveal": "never"` is irrelevant: it governs the task's
   terminal panel, not the editor the `code` binary opens. This is the mechanism that can
   raise a background window.
2. **Startup task sets `"focus": true`** — focuses the terminal widget *inside* the window
   running the task. Unlikely to be the cross-window culprit; changed anyway as cheap
   insurance.

The symptom is intermittent, so no fix can be confirmed by observation. Both plausible
causes are addressed; the documented OS-level mitigation is the cause-agnostic backstop.

## Solution

- `TASKS_JSON_TEMPLATE` drops to a **single** task ("VSCodeClaude Startup") with
  `"focus": false`. No `folderOpen` task invokes `code` any more.
- The status file **rides along with the window launch**: `launch_vscode` passes it next to
  the workspace file, so the tab opens exactly when a window is created (new session) or
  restarted (coordinator restart also goes through `launch_vscode`) — i.e. only when a
  window is being raised anyway. On reload, VS Code's editor restore brings the tab back
  with no `code` call at all.
- Troubleshooting docs gain the `ForegroundLockTimeout` registry mitigation.

## Architectural / design changes

Small and local; no new modules, no new abstractions, no signature changes.

| Area | Before | After |
|------|--------|-------|
| Generated `tasks.json` | 2 `folderOpen` tasks, one of them an IPC call into the running VS Code instance | 1 `folderOpen` task; the file is now purely "run the startup script" |
| Who opens the status file | The session window itself, on every open **and reload** | The coordinator, once per `code` invocation, as an argument to the launch |
| Focus behaviour | Startup task grabs the terminal widget | Terminal panel still reveals (`reveal: "always"`), but does not take focus |
| `launch_vscode` contract | "launch a workspace" | "launch a workspace **with its status file open**" — the single place that may legitimately raise a window |

**Key design decision (KISS):** `launch_vscode` **derives** the status-file path from the
workspace file instead of taking a new parameter:

```python
status_file = get_status_file_path(workspace_file.parent / workspace_file.stem)
```

`get_status_file_path()` (plus `STATUS_FILE_NAME`) is a new one-line helper in
`workspace.py`, next to `get_workspace_file_path`, and is also used by `create_status_file`
— so the `<session folder>/.vscodeclaude_status.txt` path is built in exactly one place
rather than duplicated between the writer and the launcher.

This is valid because `workspace.get_workspace_file_path()` is the single source of truth
for the convention `{workspace_base}/{folder_name}.code-workspace`, sitting right beside
the session folder `{workspace_base}/{folder_name}`, and **both** call sites
(`prepare_and_launch_session`, `restart_closed_sessions`) build the path through it.
Consequences: no signature change, no call-site change in `session_restart.py`, and no
churn in the ~5 existing test doubles patched as `lambda _: 9999`. The existing unused
`session_working_dir` parameter is deliberately left as-is (status quo) rather than wired
up, because using it would require editing `session_restart.py` plus 5 test mocks for zero
behavioural difference.

## Constraints & rationale (carried from the issue)

- **`reveal` stays `"always"`.** `"silent"` means "reveal only if the output is not scanned
  for errors and warnings"; the task has `"problemMatcher": []`, so nothing is scanned and
  `silent` would behave exactly like `always`. `never` is wrong too — the panel must open
  because the interactive `claude` runs in it.
- **The status file must always open**, hence the `code` call moves to `launch_vscode`
  rather than being deleted. A marker-file approach in `session_setup.py` was rejected as
  too much machinery for a now-rare symptom.
- **Unverified assumption:** that `code <workspace> <file>` opens the file inside that
  workspace's window rather than ignoring one argument. Deliberately not gated on a manual
  check — if the tab stops appearing, fall back to opening it once per folder from
  `session_setup.py` behind a marker file.
- **VS Code targets the containing window.** `.vscodeclaude_status.txt` lives inside the
  session folder, so VS Code prefers the window whose workspace contains that path.
- **The status path is passed unconditionally** (no `.exists()` guard): both call sites
  write/regenerate the status file before launching, and a guard would add a branch and a
  non-deterministic test for nothing.
- **No migration for existing sessions.** `regenerate_session_files` rewrites `tasks.json`,
  but only on the restart path — after a window has been closed. Windows open right now
  keep the stale two-task file until they restart. Acceptable; sessions self-heal.
- **`launch_vscode` raising a window is by design** — a newly created window taking focus
  is normal, and it is the only remaining `code` invocation.

## Files created / modified

### Modified — source (`src/mcp_coder/workflows/vscodeclaude/`)

| File | Change |
|------|--------|
| `templates.py` | `TASKS_JSON_TEMPLATE`: delete the "Open Status File" task; `"focus": true` → `false` |
| `workspace.py` | new `STATUS_FILE_NAME` + `get_status_file_path()` beside `get_workspace_file_path`; `create_status_file` uses it instead of an inline literal |
| `session_launch.py` | `launch_vscode`: append `get_status_file_path(...)` to the `code` invocation (both Windows and POSIX branches) |

### Modified — tests

| File | Change |
|------|--------|
| `tests/workflows/vscodeclaude/test_workspace.py` | `test_create_vscode_task`: assert exactly 1 task + `focus is False`; **new** guard test that no `folderOpen` task invokes `code` |
| `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` | `test_tasks_json_is_valid_json_template`: `len(tasks) == 2` → `== 1` (`reveal == "always"` assertion stays) |
| `tests/workflows/vscodeclaude/test_session_launch.py` | **New** test: `launch_vscode` passes the status file alongside the workspace file |

### Modified — docs

| File | Change |
|------|--------|
| `docs/coordinator-vscodeclaude.md` | New Troubleshooting subsection documenting the `ForegroundLockTimeout` mitigation |

### Verified only (no edit expected)

- `tests/workflows/vscodeclaude/test_session_launch_regenerate.py:104` — `len(tasks) > 0`
  and the `tasks[0]` assertions still hold with a single-task file.

### Not created

No new modules, packages or fixtures.

## Implementation steps

| Step | Scope | Commit |
|------|-------|--------|
| [step_1.md](./step_1.md) | `TASKS_JSON_TEMPLATE` → single task, `focus: false`; template/shape tests + guard test | 1 |
| [step_2.md](./step_2.md) | `launch_vscode` passes the status file alongside the workspace | 1 |
| [step_3.md](./step_3.md) | `ForegroundLockTimeout` troubleshooting docs | 1 |

Steps 1 and 2 are independent in code but ordered so that the status file stops being
opened by a task (step 1) only one commit before it starts being opened at launch
(step 2); on the restart path both land together in practice.

## Acceptance criteria (from the issue)

- [ ] Generated `tasks.json` contains exactly one task, and no `folderOpen` task invokes
      the `code` binary. *(step 1)*
- [ ] Startup task sets `"focus": false`. *(step 1)*
- [ ] `launch_vscode` passes `.vscodeclaude_status.txt` alongside the `.code-workspace`
      file. *(step 2)*
- [ ] Reloading an existing session window runs no `code` invocation. *(step 1 — follows
      from the deleted task, asserted by the guard test)*
- [ ] `ForegroundLockTimeout` mitigation documented in `docs/coordinator-vscodeclaude.md`.
      *(step 3)*
- [ ] Guard test present; existing tests updated and passing. *(steps 1–2)*

## Quality gates (per `CLAUDE.md`, after every step)

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

Run `./tools/format_all.sh` before committing.
