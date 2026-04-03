# Step 6: Workflow cores + CLI commands — wire up both flags

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE

### Source files (6 files):
- `src/mcp_coder/workflows/implement/core.py` — rename param + add param
- `src/mcp_coder/workflows/create_pr/core.py` — rename param + add param
- `src/mcp_coder/workflows/create_plan.py` — rename param + add param
- `src/mcp_coder/cli/commands/implement.py` — use `resolve_issue_interaction_flags()`
- `src/mcp_coder/cli/commands/create_pr.py` — use `resolve_issue_interaction_flags()`
- `src/mcp_coder/cli/commands/create_plan.py` — use `resolve_issue_interaction_flags()`

### Test files (5 files):
- `tests/workflows/implement/test_core.py`
- `tests/workflows/create_pr/test_workflow.py`
- `tests/workflows/create_plan/test_main.py`
- `tests/cli/commands/test_implement.py`
- `tests/cli/commands/test_create_pr.py`
- `tests/cli/commands/test_create_plan.py`

## WHAT

### Workflow function signature changes

**`run_implement_workflow()`:**
```python
def run_implement_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW
) -> int:
```
- All internal calls to `handle_workflow_failure()` pass both flags
- Success-path label update uses `update_issue_labels`

**`run_create_pr_workflow()`:**
```python
def run_create_pr_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW
) -> int:
```
- All internal calls to `_handle_create_pr_failure()` pass both flags
- Success-path label update uses `update_issue_labels`

**`run_create_plan_workflow()`:**
```python
def run_create_plan_workflow(
    issue_number: int,
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW
) -> int:
```
- Success-path label update uses `update_issue_labels`
- Note: `create_plan` doesn't currently use `handle_workflow_failure()` — `post_issue_comments` is accepted but not used internally yet (future-proofing the interface)

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
- Pass two bools as positional or keyword args to workflow functions

## ALGORITHM
No new algorithm — parameter renaming and wiring.

## DATA
- **CLI commands:** now pass `(update_issue_labels: bool, post_issue_comments: bool)` to workflows
- **Workflow functions:** accept and forward both flags to failure handlers and success-path label updates

## TESTS

### Update CLI command tests:

In `test_implement.py`, `test_create_pr.py`, `test_create_plan.py`:
- Change `args = argparse.Namespace(..., update_labels=False)` → `args = argparse.Namespace(..., update_issue_labels=None, post_issue_comments=None)`
- Update `mock_run_workflow.assert_called_once_with(...)` assertions to expect the two resolved bools
- Mock `resolve_issue_interaction_flags` to return `(False, False)` or `(True, True)` as needed
- Add test for `update_issue_labels=True` being passed through correctly

### Update workflow tests:

In `test_core.py` (implement), `test_workflow.py` (create_pr), `test_main.py` (create_plan):
- Rename `update_labels=...` kwargs to `update_issue_labels=...`
- Add `post_issue_comments=...` where failure handling is tested
- Verify both flags reach `handle_workflow_failure` / `_handle_create_pr_failure`

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_6.md.

Implement Step 6: wire up both flags through workflow cores and CLI commands.

This is the largest step — it connects all the pieces from Steps 1-5.

1. Update tests FIRST:
   - tests/cli/commands/test_implement.py — update args namespace, mock resolve_issue_interaction_flags
   - tests/cli/commands/test_create_pr.py — same
   - tests/cli/commands/test_create_plan.py — same
   - tests/workflows/implement/test_core.py — rename update_labels → update_issue_labels, add post_issue_comments
   - tests/workflows/create_pr/test_workflow.py — same
   - tests/workflows/create_plan/test_main.py — same

2. Modify source files:
   - src/mcp_coder/cli/commands/implement.py — use resolve_issue_interaction_flags()
   - src/mcp_coder/cli/commands/create_pr.py — same
   - src/mcp_coder/cli/commands/create_plan.py — same
   - src/mcp_coder/workflows/implement/core.py — rename param + add param + pass to handlers
   - src/mcp_coder/workflows/create_pr/core.py — same
   - src/mcp_coder/workflows/create_plan.py — same

3. Run all code quality checks (pylint, pytest, mypy)
4. Fix any issues until all checks pass
```

## COMMIT MESSAGE
```
feat: wire update_issue_labels and post_issue_comments through workflows (#661)

- Rename update_labels → update_issue_labels in all workflow functions
- Add post_issue_comments parameter to all workflow functions
- CLI commands use resolve_issue_interaction_flags() shared helper
- All failure handlers receive both flags
```
