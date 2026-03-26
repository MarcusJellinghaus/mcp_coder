# Step 3: Remove `update_labels` parameter from CLI and workflow

## Context
See [summary.md](./summary.md) for full implementation overview.

This step removes the opt-out flag. Labels will always transition — wired up in Step 4.

## WHERE
- `src/mcp_coder/cli/parsers.py` — remove `--update-labels` argument
- `src/mcp_coder/cli/commands/implement.py` — remove `update_labels` extraction and passing
- `src/mcp_coder/workflows/implement/core.py` — remove `update_labels` parameter from `run_implement_workflow()`
- `tests/cli/commands/test_implement.py` — update tests that reference `update_labels`
- `tests/workflows/implement/test_core.py` — update tests that pass `update_labels`

## WHAT

### `run_implement_workflow()` signature change
```python
# BEFORE
def run_implement_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
    update_labels: bool = False,     # ← REMOVE
) -> int:

# AFTER
def run_implement_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> int:
```

### Remove from `core.py` body
- Remove the `if update_labels and completed_tasks > 0 and not error_occurred:` block at the end (Step 7)
- The label transition will be re-added in Step 4 as an unconditional success/failure transition

### Remove from `parsers.py`
- Delete the `--update-labels` argument from `add_implement_parser()`

### Remove from `commands/implement.py`
- Remove `update_labels = getattr(args, "update_labels", False)`
- Remove `update_labels` from `run_implement_workflow()` call

## ALGORITHM
This is a pure deletion step — no new logic.

## TESTS
Update existing tests:
- In `test_implement.py`: Remove `update_labels=False` from `mock_run_workflow.assert_called_once_with(...)` calls and `argparse.Namespace(...)` constructions where `update_labels` appears
- In `test_core.py`: Remove `update_labels=True/False` from all `run_implement_workflow()` calls
- Verify tests still pass after removals

## LLM PROMPT
```
Implement Step 3 of issue #189 (see pr_info/steps/summary.md for context).

Remove the `update_labels` parameter from:
1. `run_implement_workflow()` in core.py (parameter + the Step 7 label block)
2. `add_implement_parser()` in parsers.py (--update-labels argument)
3. `execute_implement()` in commands/implement.py (extraction + passing)

Update all tests in test_implement.py and test_core.py to remove
`update_labels` references.

See pr_info/steps/step_3.md for details.
Run all quality checks after changes.
```
