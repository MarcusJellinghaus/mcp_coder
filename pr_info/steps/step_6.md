# Step 6 — `check_branch_status --fix` pre-flight

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md` only.
> TDD: write the tests first, then the implementation. Run pylint, mypy, pytest (fast unit
> markers, `-n auto`) and lint-imports; all must pass. Format with `run_format_code`, then
> make exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/check_branch_status.py`
- `tests/cli/commands/test_check_branch_status_auto_fixes.py`

## WHAT

In `_run_auto_fixes`, after the `report.ci_status != CIStatus.FAILED` early return and before the
`try:` that calls `check_and_fix_ci`:

```python
formatter_err = check_formatter_config(project_dir, warn_legacy_key=True)
if formatter_err:
    logger.error(formatter_err)
    return False
```

## HOW

- Import `check_formatter_config` from `mcp_coder.workflow_steps.commit`.
- Placement means no formatter check when there is nothing to fix (`fix_attempts == 0` or CI not failed).

## ALGORITHM

```
if fix_attempts == 0: return True          # existing
if ci_status != FAILED: return True        # existing
msg = check_formatter_config(project_dir, warn_legacy_key=True)
if msg: logger.error(msg); return False
... existing fix logic ...
```

## DATA

`bool` — `False` on a formatter config error.

## Tests

- Patch `mcp_coder.cli.commands.check_branch_status.check_formatter_config` → message, CI FAILED:
  returns False, message logged at ERROR, `check_and_fix_ci` not called.
- CI not FAILED: helper not called.
