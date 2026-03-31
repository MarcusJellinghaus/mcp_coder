# Step 5: Session Lookup + Orphan Folder Detection

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context.
> Implement Step 5: add `.to_be_deleted` exclusion in `get_session_for_issue()` in `sessions.py`,
> add `warn_orphan_folders()` to detect untracked folders on disk,
> and update the caller in `session_launch.py` to pass `workspace_base`.
> Follow TDD — write tests first, then implement.
> Run all three code quality checks (pylint, pytest, mypy) after implementation.

## WHERE

- **Modify**: `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- **Modify**: `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (pass `workspace_base` to `get_session_for_issue`)
- **Modify**: `src/mcp_coder/workflows/vscodeclaude/cleanup.py` (call `warn_orphan_folders` from `cleanup_stale_sessions`)
- **Modify**: `src/mcp_coder/workflows/vscodeclaude/__init__.py` (if signature changes need re-export updates)
- **Modify**: `tests/workflows/vscodeclaude/test_sessions.py`

## WHAT

### `get_session_for_issue()` — new optional parameter

```python
def get_session_for_issue(
    repo_full_name: str,
    issue_number: int,
    workspace_base: str,  # NEW
) -> VSCodeClaudeSession | None:
```

### `warn_orphan_folders()` — new helper function

```python
def warn_orphan_folders(workspace_base: str, repo_name: str, issue_number: int) -> None:
    """Scan disk for folders matching the issue that aren't tracked.
    
    Checks for {base} and {base}-folder\d+ folders on disk that are
    not in sessions.json and not in .to_be_deleted. Logs a warning
    for each orphan found.
    """
```

## HOW

- Import `load_to_be_deleted` from `.helpers` in `sessions.py`
- Import `re` for orphan folder pattern matching
- Import `sanitize_folder_name` from `.config` (or wherever the repo name sanitization lives) for `warn_orphan_folders`
- `workspace_base` is required (always passed by caller)

## ALGORITHM

### `get_session_for_issue` exclusion

```python
to_be_deleted = load_to_be_deleted(workspace_base)

matches = []
for session in store["sessions"]:
    if session["repo"] == repo_full_name and session["issue_number"] == issue_number:
        if Path(session["folder"]).name not in to_be_deleted:
            matches.append(session)

if len(matches) > 1:
    logger.error("Multiple active folders for %s #%d", repo_full_name, issue_number)
    return None
return matches[0] if matches else None
```

> **Note**: The multi-match detection always applies. If >1 active (non-soft-deleted) session matches, it returns `None` with an error log.

### `warn_orphan_folders`

Called from `cleanup_stale_sessions()` in `cleanup.py`. It runs after the retry loop (after retrying `.to_be_deleted` entries) and before processing stale sessions:

```python
# In cleanup_stale_sessions(), after retry loop:
if not dry_run:
    # Run orphan detection for all repos with active sessions
    for repo_name, issues in sessions_by_repo.items():
        for issue_number in issues:
            warn_orphan_folders(workspace_base, repo_name, issue_number)
```

```python
sanitized_repo = sanitize_folder_name(repo_name)
base_name = f"{sanitized_repo}_{issue_number}"
pattern = re.compile(rf"^{re.escape(base_name)}(-folder\d+)?$")
to_be_deleted = load_to_be_deleted(workspace_base)
session_folders = {Path(s["folder"]).name for s in load_sessions()["sessions"]}

for entry in Path(workspace_base).iterdir():
    if entry.is_dir() and pattern.match(entry.name):
        if entry.name not in to_be_deleted and entry.name not in session_folders:
            logger.warning("Orphan folder detected: %s", entry.name)
```

### Caller update in `session_launch.py`

```python
# In process_eligible_issues():
existing = get_session_for_issue(
    repo_full_name,
    issue["number"],
    workspace_base=vscodeclaude_config["workspace_base"],
)
```

## DATA

- `workspace_base: str` — required, path to workspace directory
- Return values unchanged for `get_session_for_issue`
- `warn_orphan_folders` returns `None`, side effect is logging

## TESTS (`test_sessions.py`)

### Session lookup tests

```python
- test_get_session_for_issue_excludes_soft_deleted(tmp_path)
    → session found in JSON but folder in .to_be_deleted → returns None
- test_get_session_for_issue_returns_non_deleted(tmp_path)
    → session found, folder not in .to_be_deleted → returns session
- test_get_session_for_issue_multiple_active_returns_none(tmp_path)
    → two sessions for same issue, neither deleted → log error, return None
```

### Orphan folder detection tests

```python
- test_warn_orphan_folders_logs_warning_for_untracked(tmp_path)
    → folder on disk not in sessions.json or .to_be_deleted → warning logged
- test_warn_orphan_folders_ignores_tracked_sessions(tmp_path)
    → folder on disk in sessions.json → no warning
- test_warn_orphan_folders_ignores_to_be_deleted(tmp_path)
    → folder on disk in .to_be_deleted → no warning
- test_warn_orphan_folders_ignores_unrelated_folders(tmp_path)
    → folder on disk not matching pattern → no warning
```

## COMMIT MESSAGE

```
feat(vscodeclaude): session lookup excludes soft-deleted, detect orphan folders

Filter .to_be_deleted entries from get_session_for_issue(). Add
warn_orphan_folders() to detect untracked folders on disk. Log
error if multiple active sessions found for same issue.
```
