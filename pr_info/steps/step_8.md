# Step 8 — Build the workspace file with `json.dumps`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_8.md`), then implement Step 8 only. `create_workspace_file` builds a dict and writes `json.dumps`, so quotes and backslashes in the issue title can no longer produce invalid JSON. Remove `WORKSPACE_FILE_TEMPLATE`. Write the test first, then the implementation. Run the checks from the summary, then make one commit.

## Rationale

`WORKSPACE_FILE_TEMPLATE.format` inserts values into JSON string literals without escaping them. A title containing `"` or `\` yields invalid JSON. VSCode then most likely ignores `window.title`, which means a permanent, now authoritative, title miss. Serializing a dict removes the escaping problem entirely, and the truncation can no longer split an escape sequence.

## WHERE / WHAT

**`src/mcp_coder/workflows/vscodeclaude/workspace.py`** (`create_workspace_file`, same signature and return)

```python
workspace = {
    "folders": [{"path": f"./{folder_name}"}],
    "settings": {
        "window.title": f"[#{issue_number} {stage_short}] {title_short} - {repo_name}",
        "task.allowAutomaticTasks": "on",
    },
}
content = json.dumps(workspace, indent=4) + "\n"
```

- Keep the existing truncation (`title_short`) and `stage_short` logic.
- Remove the local `from .templates import WORKSPACE_FILE_TEMPLATE`.
- Add `import json` if it isn't imported already.
- `json.dumps` defaults to `ensure_ascii=True`. Pass `ensure_ascii=False` so non-ASCII titles stay readable; the file is written as UTF-8.

**`src/mcp_coder/workflows/vscodeclaude/templates.py`**
- Delete `WORKSPACE_FILE_TEMPLATE` and its comment.
- Drop it from the module docstring list (~line 18).

**`tests/cli/commands/coordinator/test_vscodeclaude_cli.py`**
- Remove the `WORKSPACE_FILE_TEMPLATE` import and the template-format test (~lines 31–40). `test_workspace.py` covers the behaviour.

## Tests (write first)

**`test_workspace.py`**
- `create_workspace_file(..., issue_title='Fix "quoted" C:\\path title', ...)`.
- The file parses with `json.loads`.
- `settings["window.title"]` contains `"quoted"` and `C:\path`. Use a title of 30 characters or fewer, or assert on the truncated prefix.
- `folders[0]["path"] == "./<folder_name>"`.

Existing workspace tests use `json.loads` / substring checks and must pass unchanged. If one asserts on exact whitespace, adapt it to `json.loads`.

## Verification

- `search_files` for `WORKSPACE_FILE_TEMPLATE` returns no hits.

## Commit

`fix(vscodeclaude): serialize workspace file with json.dumps`
