# Step 4: Status Filtering + Session Lookup Safety Check

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context.
> Implement Step 4: filter soft-deleted folders from `display_status_table()` in `status.py`,
> add `.to_be_deleted` exclusion in `get_session_for_issue()` in `sessions.py`,
> and update CLI callers to pass `workspace_base`.
> Follow TDD — write tests first, then implement.
> Run all three code quality checks (pylint, pytest, mypy) after implementation.

## WHERE

- **Modify**: `src/mcp_coder/workflows/vscodeclaude/status.py`
- **Modify**: `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- **Modify**: `src/mcp_coder/cli/commands/coordinator/commands.py`
- **Modify**: `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (pass `workspace_base` to `get_session_for_issue`)
- **Modify**: `src/mcp_coder/workflows/vscodeclaude/__init__.py` (if signature changes need re-export updates)
- **Modify**: `tests/workflows/vscodeclaude/test_status_display.py`
- **Modify**: `tests/workflows/vscodeclaude/test_sessions.py`

## WHAT

### `display_status_table()` — new optional parameter

```python
def display_status_table(
    sessions: list[VSCodeClaudeSession],
    eligible_issues: list[tuple[str, IssueData]],
    repo_filter: str | None = None,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
    issues_without_branch: set[tuple[str, int]] | None = None,
    workspace_base: str | None = None,  # NEW
) -> None:
```

### `get_session_for_issue()` — new optional parameter

```python
def get_session_for_issue(
    repo_full_name: str,
    issue_number: int,
    workspace_base: str | None = None,  # NEW
) -> VSCodeClaudeSession | None:
```

## HOW

- Import `load_to_be_deleted` from `.helpers` in both `status.py` and `sessions.py`
- `workspace_base` is optional (`None`) for backward compatibility
- CLI callers load config and pass `workspace_base`

## ALGORITHM

### `display_status_table` filtering

```python
# At top of function, after cache refresh:
to_be_deleted: set[str] = set()
if workspace_base:
    to_be_deleted = load_to_be_deleted(workspace_base)

# In session loop, after folder_path assignment:
if folder_path.name in to_be_deleted:
    continue  # skip soft-deleted sessions
```

### `get_session_for_issue` exclusion

```python
to_be_deleted: set[str] = set()
if workspace_base:
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

### Caller updates

```python
# In execute_coordinator_vscodeclaude_status() in commands.py:
vscodeclaude_config = load_vscodeclaude_config()
display_status_table(
    ...,
    workspace_base=vscodeclaude_config["workspace_base"],
)

# In process_eligible_issues() in session_launch.py:
existing = get_session_for_issue(
    repo_full_name,
    issue["number"],
    workspace_base=vscodeclaude_config["workspace_base"],
)
```

## DATA

- `workspace_base: str | None` — optional for backward compat
- Return values unchanged
- No new data structures

## TESTS

### `test_status_display.py` additions

```python
- test_display_status_table_hides_soft_deleted_sessions(tmp_path)
    → session with folder in .to_be_deleted not shown in output
- test_display_status_table_shows_non_deleted_sessions(tmp_path)
    → session with folder NOT in .to_be_deleted still shown
- test_display_status_table_works_without_workspace_base()
    → backward compat: workspace_base=None shows all sessions
```

### `test_sessions.py` additions

```python
- test_get_session_for_issue_excludes_soft_deleted(tmp_path)
    → session found in JSON but folder in .to_be_deleted → returns None
- test_get_session_for_issue_returns_non_deleted(tmp_path)
    → session found, folder not in .to_be_deleted → returns session
- test_get_session_for_issue_multiple_active_returns_none(tmp_path)
    → two sessions for same issue, neither deleted → log error, return None
- test_get_session_for_issue_works_without_workspace_base()
    → backward compat: workspace_base=None returns first match (existing behavior)
```

## COMMIT MESSAGE

```
feat(vscodeclaude): hide soft-deleted folders from status and session lookup

Filter .to_be_deleted entries from display_status_table() and
get_session_for_issue(). Pass workspace_base from CLI entry points.
Log error if multiple active folders found for same issue.
```
