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
    dry_run: bool = True,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
    workspace_base: str | None = None,  # NEW — needed for .to_be_deleted
) -> dict[str, list[str]]:
```

### `delete_session_folder()` — soft-delete on failure

```python
def delete_session_folder(
    session: VSCodeClaudeSession,
    workspace_base: str | None = None,  # NEW
    was_clean: bool = False,            # NEW — caller knows pre-deletion git status
) -> bool:
```

### Caller update in `commands.py`

```python
# In execute_coordinator_vscodeclaude():
cleanup_stale_sessions(
    dry_run=False,
    cached_issues_by_repo=cached_issues_by_repo,
    workspace_base=vscodeclaude_config["workspace_base"],  # NEW
)
```

## HOW

- Import `load_to_be_deleted`, `add_to_be_deleted`, `remove_from_to_be_deleted` from `.helpers`
- Import `safe_delete_folder` (already imported)
- `workspace_base` is optional (`None`) for backward compatibility with existing tests

## ALGORITHM

### Retry logic (at start of `cleanup_stale_sessions`, before stale session processing)

```
if workspace_base and not dry_run:
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

### Soft-delete on failure (in `delete_session_folder`, when folder deletion fails)

```
# Current: return False on failure
# New: if was_clean and workspace_base:
#   1. Always delete .code-workspace file
#   2. add_to_be_deleted(workspace_base, folder_name)
#   3. remove_session(session["folder"])
#   4. log INFO "Soft-deleted: {folder_name}"
#   (still return False — folder wasn't actually deleted)
```

### Always delete `.code-workspace` (in `delete_session_folder`)

Move workspace file deletion **before** folder deletion attempt, or make it happen regardless of folder deletion success. The workspace file should always be cleaned up.

## DATA

- `workspace_base: str | None` — optional for backward compat
- `was_clean: bool` — True when caller verified git status was "Clean" before calling
- Return values unchanged

## TESTS (add to `test_cleanup.py`)

```python
# Retry logic
- test_cleanup_retries_to_be_deleted_entries() → folder deleted, entry removed
- test_cleanup_retry_removes_stale_entry_if_folder_missing() → entry removed when folder gone
- test_cleanup_retry_skipped_in_dry_run() → no retry when dry_run=True
- test_cleanup_retry_skipped_when_no_workspace_base() → backward compat

# Soft-delete on failure
- test_delete_session_folder_soft_deletes_on_failure_when_clean()
    → folder deletion fails, workspace file deleted, entry added, session removed
- test_delete_session_folder_no_soft_delete_when_dirty()
    → folder deletion fails but was_clean=False, no .to_be_deleted entry
- test_delete_session_folder_no_soft_delete_without_workspace_base()
    → backward compat: was_clean=True but no workspace_base, no entry added
- test_delete_session_folder_always_deletes_workspace_file()
    → workspace file deleted even when folder deletion fails
```

## COMMIT MESSAGE

```
feat(vscodeclaude): soft-delete on cleanup failure, retry on next run

When folder deletion fails for a clean session, add it to
.to_be_deleted registry and remove from sessions.json. Always delete
the .code-workspace file. Retry soft-deleted entries at the start
of each --cleanup run.
```
