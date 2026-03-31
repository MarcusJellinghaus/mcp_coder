# Step 4: Status Filtering

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context.
> Implement Step 4: filter soft-deleted folders from `display_status_table()` in `status.py`,
> and update the CLI caller to pass `workspace_base`.
> Follow TDD — write tests first, then implement.
> Run all three code quality checks (pylint, pytest, mypy) after implementation.

## WHERE

- **Modify**: `src/mcp_coder/workflows/vscodeclaude/status.py`
- **Modify**: `src/mcp_coder/cli/commands/coordinator/commands.py` (pass `workspace_base` to `display_status_table`)
- **Modify**: `tests/workflows/vscodeclaude/test_status_display.py`

## WHAT

### `display_status_table()` — new optional parameter

```python
def display_status_table(
    sessions: list[VSCodeClaudeSession],
    eligible_issues: list[tuple[str, IssueData]],
    workspace_base: str,  # NEW — required, before optional params
    repo_filter: str | None = None,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
    issues_without_branch: set[tuple[str, int]] | None = None,
) -> None:
```

## HOW

- Import `load_to_be_deleted` from `.helpers` in `status.py`
- `workspace_base` is required (always passed by caller)
- CLI caller loads config and passes `workspace_base`

## ALGORITHM

### `display_status_table` filtering

```python
# At top of function, after cache refresh:
to_be_deleted = load_to_be_deleted(workspace_base)

# In session loop, after folder_path assignment:
if folder_path.name in to_be_deleted:
    continue  # skip soft-deleted sessions
```

> **Note**: Soft-deleted sessions are intentionally excluded from `session_keys`. This makes their issues appear as available for new sessions, which is correct — the old folder is soft-deleted, and `get_working_folder_path` (step 3) will pick a suffix name for the new session.

### Caller update in `commands.py`

```python
# In execute_coordinator_vscodeclaude_status():
vscodeclaude_config = load_vscodeclaude_config()
display_status_table(
    ...,
    workspace_base=vscodeclaude_config["workspace_base"],
)
```

## DATA

- `workspace_base: str` — required, path to workspace directory
- Return values unchanged
- No new data structures

## TESTS (`test_status_display.py`)

```python
- test_display_status_table_hides_soft_deleted_sessions(tmp_path)
    → session with folder in .to_be_deleted not shown in output
- test_display_status_table_shows_non_deleted_sessions(tmp_path)
    → session with folder NOT in .to_be_deleted still shown
```

## COMMIT MESSAGE

```
feat(vscodeclaude): hide soft-deleted folders from status

Filter .to_be_deleted entries from display_status_table(). Pass
workspace_base from CLI entry point.
```
