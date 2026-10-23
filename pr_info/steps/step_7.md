# Step 7 — Migrate `tests/workflows/vscodeclaude/test_session_restart*` (4 files)

## LLM prompt

> Read `pr_info/steps/summary.md` (especially "Shared migration rules"), then implement
> `pr_info/steps/step_7.md` exactly. Run the checks listed in the summary, including the
> full fast pytest suite; all must pass. Produce one commit.

## WHERE
- `tests/workflows/vscodeclaude/test_session_restart.py`
- `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py`
- `tests/workflows/vscodeclaude/test_session_restart_cache.py`
- `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py`

## WHAT
Replace every full issue literal (mostly `x: IssueData = {...}` and untyped dicts fed
into `Mock.return_value` / cache lists) with `make_issue_data(...)` per the shared rules.
Keep closed-state values (`state="closed"`) and labels as overrides.

## HOW
`from tests.github_factories import make_issue_data`. Retype `dict[str, Any]` /
`list[dict[str, Any]]` receivers to `IssueData` / `list[IssueData]` where mypy requires.
Remove unused imports.

## DATA
Same values per site as before.

## Done when
No line in these 4 files matches `"locked":|\blocked=`.
