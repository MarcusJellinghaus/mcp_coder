# Step 2: Cleanup — Retry + Soft-Delete on Failure

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context.
> Implement Step 2: modify `cleanup.py` to retry `.to_be_deleted` entries and soft-delete on failure.
> Update the CLI caller to pass `workspace_base`.
> Follow TDD — write tests first, then implement.
> Run all three code quality checks (pylint, pytest, mypy) after implementation.

## WHERE

- **Modify**: `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
- **Modify**: `src/mcp_coder/cli/commands/coordinator/commands.py` (pass `workspace_base`)
- **Modify**: `tests/workflows/vscodeclaude/test_cleanup.py`

## WHAT

### `cleanup_stale_sessions()` — new parameter + retry logic

```python
def cleanup_stale_sessions(
    workspace_base: str,  # NEW — required, before optional params
    dry_run: bool = True,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> dict[str, list[str]]:
```

### `delete_session_folder()` — soft-delete on failure

```python
def delete_session_folder(
    session: VSCodeClaudeSession,
    workspace_base: str,  # NEW — required, before optional params
    was_clean: bool = False,            # NEW — caller knows pre-deletion git status
) -> bool:
```

### Caller update in `commands.py`

```python
# In execute_coordinator_vscodeclaude(), TWO call sites:
# 1. dry_run=True call:
cleanup_stale_sessions(
    dry_run=True,
    cached_issues_by_repo=cached_issues_by_repo,
    workspace_base=vscodeclaude_config["workspace_base"],  # NEW
)
# 2. dry_run=False call:
cleanup_stale_sessions(
    dry_run=False,
    cached_issues_by_repo=cached_issues_by_repo,
    workspace_base=vscodeclaude_config["workspace_base"],  # NEW
)
```

## HOW

- Import `load_to_be_deleted`, `add_to_be_deleted`, `remove_from_to_be_deleted` from `.helpers`
- Import `safe_delete_folder` (already imported)
- `workspace_base` is required (always passed by caller)

## ALGORITHM

### Retry logic (at start of `cleanup_stale_sessions`, before stale session processing)

```
if not dry_run:
    to_delete = load_to_be_deleted(workspace_base)
    for folder_name in list(to_delete):
        folder_path = Path(workspace_base) / folder_name
        if not folder_path.exists():
            remove_from_to_be_deleted(workspace_base, folder_name)
            log INFO "Removed stale .to_be_deleted entry: {folder_name}"
            continue
        result = safe_delete_folder(folder_path)
        if result.success:
            remove_from_to_be_deleted(workspace_base, folder_name)
            log INFO "Retry-deleted soft-deleted folder: {folder_name}"
```

### Always delete `.code-workspace` (in `delete_session_folder`)

Delete the `.code-workspace` file **before** attempting folder deletion. The workspace file should always be cleaned up regardless of folder deletion outcome.

> **Note**: This applies to ALL deletion paths (not just soft-delete). Even if `was_clean=False`, the workspace file is removed. This matches requirement 1: always delete `.code-workspace`.

```
# Before folder deletion attempt:
# Note: construct workspace file path using workspace_base for consistency
workspace_file = Path(workspace_base) / (Path(session["folder"]).name + ".code-workspace")
if workspace_file.exists():
    workspace_file.unlink()
```

### Soft-delete on failure (in `delete_session_folder`, when folder deletion fails)

```
# Current: return False on failure
# New: if was_clean:
#   1. add_to_be_deleted(workspace_base, folder_name)
#   2. remove_session(session["folder"])
#   3. log INFO "Soft-deleted: {folder_name}"
#   (still return False — folder wasn't actually deleted)
# (.code-workspace already deleted above)
```

> **Note**: The existing `remove_session` call on the success path inside `delete_session_folder` is preserved. The new soft-delete path adds a second `remove_session` call on the failure+clean path only.

### Second call site: `cleanup_stale_sessions` empty-directory case

In `cleanup_stale_sessions`, there is a second call to `delete_session_folder` for folders with "No Git" / "Error" status (empty directories). This call passes `was_clean=False` (the default), so empty folders are NOT soft-deleted on failure — they simply fail and are left as-is.

## DATA

- `workspace_base: str` — required, path to workspace directory
- `was_clean: bool` — True when caller verified git status was "Clean" before calling
- Return values unchanged

## TESTS (add to `test_cleanup.py`)

```python
# Retry logic
- test_cleanup_retries_to_be_deleted_entries() → folder deleted, entry removed
- test_cleanup_retry_removes_stale_entry_if_folder_missing() → entry removed when folder gone
- test_cleanup_retry_skipped_in_dry_run() → no retry when dry_run=True
# Soft-delete on failure
- test_delete_session_folder_soft_deletes_on_failure_when_clean()
    → folder deletion fails, workspace file deleted, entry added, session removed
- test_delete_session_folder_no_soft_delete_when_dirty()
    → folder deletion fails but was_clean=False, no .to_be_deleted entry
- test_delete_session_folder_always_deletes_workspace_file()
    → workspace file deleted even when folder deletion fails
- test_delete_session_folder_handles_workspace_file_deletion_failure()
    → workspace file deletion raises OSError, folder deletion still attempted
- test_cleanup_soft_delete_then_retry_succeeds(tmp_path)
    → First call: folder deletion fails for clean session, entry added to .to_be_deleted.
      Second call: retry succeeds, entry removed from .to_be_deleted.
```

## COMMIT MESSAGE

```
feat(vscodeclaude): soft-delete on cleanup failure, retry on next run

When folder deletion fails for a clean session, add it to
.to_be_deleted registry and remove from sessions.json. Always delete
the .code-workspace file. Retry soft-deleted entries at the start
of each --cleanup run.
```
