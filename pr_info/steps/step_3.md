# Step 3 — Rebase: formatter pre-flight in `_preflight`, fix loop via `run_formatters`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` only.
> TDD: write the tests first, then the implementation. Run pylint, mypy, pytest (fast unit
> markers, `-n auto`) and lint-imports; all must pass. Format with `run_format_code`, then
> make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/rebase.py`
- `tests/workflows/rebase/test_guards.py` (or wherever `_preflight` is tested)
- `tests/workflows/rebase/test_workflow.py`

## WHAT

- `_preflight(project_dir) -> str | None`: last check returns
  `check_formatter_config(project_dir, warn_legacy_key=True)`.
- Regression-fix loop (`rebase.py:612`): `run_format_code(project_dir)` → `run_formatters(project_dir)`;
  return value ignored.

## HOW

- Imports: `from mcp_coder.workflow_steps.commit import check_formatter_config, run_formatters`;
  drop `from mcp_coder.mcp_tools_py import run_format_code`.
- Extend `_preflight`'s docstring "Checks, in order" list with "a resolvable formatter configuration".
- Caller is unchanged: it already logs `"Pre-flight failed: %s"` and returns `2` before any git
  mutation or LLM call.
- A `FormatterConfigError` from the fix loop is already handled by the existing
  `except Exception` (reset to `pre_sha`, return 1) — no change.

## ALGORITHM

```
_preflight(p):
    ... existing guards (unchanged) ...
    return check_formatter_config(p, warn_legacy_key=True)
```

## DATA

`_preflight` → `None` | message; `run_rebase_workflow` → `2` on a formatter config error.

## Tests

- `_preflight` returns the message when `mcp_coder.workflows.rebase.check_formatter_config`
  is patched to return `"No formatter declared: ..."`; returns None when it returns None.
- `run_rebase_workflow` with that patch → returns 2, the LLM helper (`_prompt_in_session`) not called.
- `tests/workflows/rebase/test_workflow.py:75-77, 121, 412`: patch
  `mcp_coder.workflows.rebase.run_formatters` instead of `run_format_code`; assert it is called in
  the fix loop.
- `format_code = false` → no formatting: covered by step 2's `run_formatters` gate; add one test
  asserting the rebase fix loop calls `run_formatters` (not the wrapper).
