# Step 3 — `get_workspace_file_path` helper + orphan workspace cleanup (Item #5)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`) in
> full. Implement only what this step describes. Follow TDD: write failing
> tests first, then implementation, then run the three MCP quality checks.
> One commit at the end.

## Goal

Break the "orphan workspace file → false-active → cleanup skipped → orphan
workspace file" loop. Tighten `session_has_artifacts` to require the folder.
Auto-delete orphan `.code-workspace` files in the `Missing` cleanup branch.
Funnel the workspace-file path through one helper to keep the pattern in a
single place.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/workspace.py` (new helper, refactor
  one call site)
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py` (refactor one call site,
  extend `Missing` branch)
- `src/mcp_coder/workflows/vscodeclaude/sessions.py` (tighten
  `session_has_artifacts`)
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py` (refactor one
  inline construction at line 396 — see HOW)
- `src/mcp_coder/workflows/vscodeclaude/__init__.py` (re-export the helper if
  needed by tests; otherwise internal)
- `tests/workflows/vscodeclaude/test_workspace.py`
- `tests/workflows/vscodeclaude/test_sessions.py`
- `tests/workflows/vscodeclaude/test_cleanup.py`

## WHAT — function signatures

```python
# workspace.py
def get_workspace_file_path(workspace_base: str, folder_name: str) -> Path:
    """Return the `.code-workspace` file path for a session folder."""
    return Path(workspace_base) / f"{folder_name}.code-workspace"

# sessions.py
def session_has_artifacts(folder: str) -> bool:
    """True when the working folder exists on disk."""
    return Path(folder).exists()
```

## HOW — integration points

- Refactor four sites to use the helper:
  - `workspace.py:create_workspace_file` — replace the inline construction
    near line 422.
  - `cleanup.py:delete_session_folder` — replace the inline construction
    near line 230.
  - `cleanup.py:cleanup_stale_sessions` — new use inside the `Missing` branch
    (see below).
  - `session_restart.py` near line 396 — replace
    `workspace_file = workspace_base / f"{folder_name}.code-workspace"` with
    `workspace_file = get_workspace_file_path(str(workspace_base), folder_name)`
    (or pass `Path` if the helper accepts it — keep signatures consistent).
    Confirm the exact line via `search_files` before editing.
- Drop the workspace-file branch in `session_has_artifacts`; update its
  docstring accordingly.
- Extend the `Missing` branch in `cleanup_stale_sessions`:

```python
elif git_status == "Missing":
    workspace_file = get_workspace_file_path(workspace_base, Path(folder).name)
    if dry_run:
        print(f"Would remove session (folder missing): {folder}")
    else:
        if workspace_file.exists():
            workspace_file.unlink()
        remove_session(folder)
        print(f"Removed session (folder missing): {folder}")
        result["deleted"].append(folder)
```

## ALGORITHM

```
# session_has_artifacts (new):
return Path(folder).exists()

# Missing cleanup branch (new orphan-unlink):
workspace_file = get_workspace_file_path(workspace_base, folder_name)
if workspace_file.exists():
    workspace_file.unlink()
remove_session(folder)
```

## DATA

- Helper return: `pathlib.Path`.
- `session_has_artifacts` return: `bool` (unchanged signature).
- `cleanup_stale_sessions` return: `dict[str, list[str]]` (unchanged shape;
  orphan workspace deletion adds the folder to `result["deleted"]` like
  today).

## Tests (write first)

1. **Helper purity**:
   `get_workspace_file_path("/tmp/ws", "mcp_coder_123") ==
   Path("/tmp/ws/mcp_coder_123.code-workspace")`.
2. **`session_has_artifacts` tightening**: temp folder absent, workspace file
   present in `workspace_base` → returns `False`. Drop the previous
   workspace-only positive case.
3. **Orphan cleanup integration**: in a tmp `workspace_base`, write a session
   record with deleted `folder` and a present `.code-workspace` file. Mock
   `get_stale_sessions` to yield this session with `git_status="Missing"`.
   Call `cleanup_stale_sessions(..., dry_run=False)`. Assert session removed
   from store **and** workspace file unlinked.
4. **Refactor sanity**: existing tests for `create_workspace_file` and
   `delete_session_folder` continue to pass without modification — the helper
   is a pure substitution.

## Done when

- All tests pass.
- mypy, pylint clean.
- One commit: tests + implementation.
