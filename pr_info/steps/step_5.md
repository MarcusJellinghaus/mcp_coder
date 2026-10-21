# Step 5 — fix-ci pre-flight

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md` only.
> TDD: write the tests first, then the implementation. Run pylint, mypy, pytest (fast unit
> markers, `-n auto`) and lint-imports; all must pass. Format with `run_format_code`, then
> make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/fix_ci/core.py`
- `src/mcp_coder/workflow_steps/ci.py` (docstring only)
- `tests/workflows/fix_ci/test_core.py`

## WHAT

Top of `body()` in `run_fix_ci_workflow`, before `get_current_branch_name`:

```python
formatter_err = check_formatter_config(project_dir, warn_legacy_key=True)
if formatter_err:
    return _fail(
        project_dir, "General", "Formatter configuration", formatter_err,
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
```

`ci.py` `check_and_fix_ci` docstring `Raises:` gains one short entry:

```
        FormatterConfigError: From run_formatters on invalid formatter config.
```

## HOW

- Import `check_formatter_config` from `mcp_coder.workflow_steps.commit`.
- `ci.py` is at 725 of 750 lines — keep the docstring addition to 1–2 lines; no code change there.
- Backstop: a `FormatterConfigError` from `check_and_fix_ci` reaches `run_guarded` (only LLM errors
  are caught in `body()`). No change.

## ALGORITHM

```
msg = check_formatter_config(project_dir, warn_legacy_key=True)
if msg: return _fail(project_dir, "General", "Formatter configuration", msg, ...)
... existing body ...
```

## DATA

Returns `1`; comment `**Category:** General / **Stage:** Formatter configuration / **Error:** <msg>`.

## Tests

- Patch `mcp_coder.workflows.fix_ci.core.check_formatter_config` → message: returns 1,
  `handle_workflow_failure` called with stage `"Formatter configuration"` and the message,
  `check_and_fix_ci` not called.
