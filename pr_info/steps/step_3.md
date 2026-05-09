# Step 3 — Platform-aware `create_vscode_task`

**Reference:** [summary.md](./summary.md) — issue #963.

## Goal

`tasks.json` currently uses `script_path.name` as the `command` value. On Windows that's a bare `.bat` file, which works. On POSIX, a bare filename in a shell task is not executed from the workspace folder — we need `./<name>`. This step adds that branch.

## WHERE

- **Modify:** `src/mcp_coder/workflows/vscodeclaude/workspace.py` — function `create_vscode_task`
- **Modify:** `tests/workflows/vscodeclaude/test_workspace.py`

## WHAT

### `workspace.py` — `create_vscode_task(folder_path: Path, script_path: Path) -> None`

Signature unchanged. Inside the function, derive the `command` string from `platform.system()`:

- Windows: `script_path.name` (current behavior).
- POSIX: `f"./{script_path.name}"`.

Pass the derived value into `TASKS_JSON_TEMPLATE.format(script_path=...)`. The template itself is unchanged.

## HOW

- Single-point branch in Python; no template changes. This keeps `TASKS_JSON_TEMPLATE` a pure literal.
- `platform.system() == "Windows"` is the same idiom already used elsewhere in the module.

## ALGORITHM

```
command_str = script_path.name if platform.system() == "Windows" else f"./{script_path.name}"
content = TASKS_JSON_TEMPLATE.format(script_path=command_str)
write content to folder_path/.vscode/tasks.json
```

## DATA

- Function still returns `None` and writes the same file path.
- `tasks.json` schema is unchanged; only the `command` field's value differs across platforms.

## Tests (write first)

In `tests/workflows/vscodeclaude/test_workspace.py`, add tests that:

1. **Windows**: monkeypatch `platform.system` → `"Windows"`, call `create_vscode_task(tmp_path, tmp_path / ".vscodeclaude_start.bat")`, parse the resulting `tasks.json`, assert `tasks[0]["command"] == ".vscodeclaude_start.bat"`.
2. **Darwin**: same flow with a `.sh` script, assert `tasks[0]["command"] == "./.vscodeclaude_start.sh"`.
3. **Linux**: same as Darwin.

A single parametrized test covers all three:

```python
@pytest.mark.parametrize("system,script_name,expected_command", [
    ("Windows", ".vscodeclaude_start.bat", ".vscodeclaude_start.bat"),
    ("Darwin",  ".vscodeclaude_start.sh",  "./.vscodeclaude_start.sh"),
    ("Linux",   ".vscodeclaude_start.sh",  "./.vscodeclaude_start.sh"),
])
def test_create_vscode_task_command_per_platform(...): ...
```

## Acceptance

- New parametrized test passes.
- Existing `create_vscode_task` tests still pass (Windows behavior unchanged).
- pylint, mypy, pytest clean.

## LLM prompt

> Implement Step 3 from `pr_info/steps/step_3.md`, using `pr_info/steps/summary.md` for context.
>
> In `src/mcp_coder/workflows/vscodeclaude/workspace.py`, modify `create_vscode_task` so that the `command` field passed to `TASKS_JSON_TEMPLATE` is `script_path.name` on Windows and `f"./{script_path.name}"` on POSIX. Do not change `TASKS_JSON_TEMPLATE` itself.
>
> Write the parametrized test in `tests/workflows/vscodeclaude/test_workspace.py` **first**. Use `monkeypatch.setattr` on `mcp_coder.workflows.vscodeclaude.workspace.platform.system` and parse the generated JSON with `json.loads`.
>
> Run the three required quality checks per `.claude/CLAUDE.md`. One commit, message: `Emit ./<script> in tasks.json on POSIX (#963)`.
