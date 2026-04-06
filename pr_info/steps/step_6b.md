# Step 6b: CLI commands — use resolve_issue_interaction_flags()

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE

### Source files (3 files):
- `src/mcp_coder/cli/commands/implement.py` — use `resolve_issue_interaction_flags()`
- `src/mcp_coder/cli/commands/create_pr.py` — use `resolve_issue_interaction_flags()`
- `src/mcp_coder/cli/commands/create_plan.py` — use `resolve_issue_interaction_flags()`

### Test files (3 files):
- `tests/cli/commands/test_implement.py`
- `tests/cli/commands/test_create_pr.py`
- `tests/cli/commands/test_create_plan.py`

## WHAT

### CLI command changes (all three)

Replace:
```python
update_labels = getattr(args, "update_labels", False)
return run_*_workflow(..., update_labels)
```

With:
```python
from ..utils import resolve_issue_interaction_flags

update_issue_labels, post_issue_comments = resolve_issue_interaction_flags(args, project_dir)
return run_*_workflow(..., update_issue_labels, post_issue_comments)
```

## HOW
- Import `resolve_issue_interaction_flags` from `..utils` in each CLI command
- Remove `getattr(args, "update_labels", False)` pattern
- Pass two bools as keyword args to workflow functions

## ALGORITHM
No new algorithm — wiring only.

## DATA
- **CLI commands:** now pass `(update_issue_labels: bool, post_issue_comments: bool)` to workflows

## TESTS

### Update CLI command tests:

In `test_implement.py`, `test_create_pr.py`, `test_create_plan.py`:
- Change `args = argparse.Namespace(..., update_labels=False)` → `args = argparse.Namespace(..., update_issue_labels=None, post_issue_comments=None)`
- Update `mock_run_workflow.assert_called_once_with(...)` assertions to expect the two resolved bools
- Mock `resolve_issue_interaction_flags` to return `(False, False)` or `(True, True)` as needed
- Add test for `update_issue_labels=True` being passed through correctly

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_6b.md.

Implement Step 6b: update CLI commands to use resolve_issue_interaction_flags().

1. Update tests FIRST:
   - tests/cli/commands/test_implement.py — update args namespace, mock resolve_issue_interaction_flags
   - tests/cli/commands/test_create_pr.py — same
   - tests/cli/commands/test_create_plan.py — same

2. Modify source files:
   - src/mcp_coder/cli/commands/implement.py — use resolve_issue_interaction_flags()
   - src/mcp_coder/cli/commands/create_pr.py — same
   - src/mcp_coder/cli/commands/create_plan.py — same

3. Run all code quality checks (pylint, pytest, mypy)
4. Fix any issues until all checks pass
```

## COMMIT MESSAGE
```
feat: CLI commands use resolve_issue_interaction_flags (#661)

Replace getattr(args, "update_labels", False) with shared
resolve_issue_interaction_flags() helper in implement, create-pr,
and create-plan CLI commands.
```
