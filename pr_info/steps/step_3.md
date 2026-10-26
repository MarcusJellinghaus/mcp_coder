# Step 3 — `failure_handling.get_diff_stat`

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement step 3 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(failure-handling): diff stat via mcp_workspace_git`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `git_diff` (from `mcp_workspace.git_operations.read_operations`)
- `src/mcp_coder/workflow_utils/failure_handling.py` — `get_diff_stat` (~line 119); drop the `execute_command` import
- `tests/workflow_utils/test_failure_handling.py` (~86–100)

## WHAT

```python
_NO_DIFF = "No changes found"  # git_diff's sentinel for an empty diff

def get_diff_stat(project_dir: Path) -> str:
    try:
        stat = git_diff(project_dir, ["HEAD", "--stat"])
    except Exception:  # pylint: disable=broad-exception-caught
        return ""  # git_diff raises on a non-repo or git failure
    return "" if stat == _NO_DIFF else stat
```

`git_diff` truncates at `max_lines=100` — acceptable for a failure summary (issue Constraints).
`"HEAD"` is a non-flag arg and passes upstream validation; `--stat` disables compact mode upstream.

## Tests (write first)

- patched `git_diff` returns `" a.py | 2 +-\n 1 file changed"` → returned unchanged; called with `(project_dir, ["HEAD", "--stat"])`.
- returns `"No changes found"` → `""`.
- raises `ValueError` → `""`.
- Remove the old argv assertion and the `execute_command` patch.

## DATA

- `str` — diff stat or `""`.
