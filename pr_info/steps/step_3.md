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
- Issue item 9, remaining entry points: one test each that the entry point formats only through
  the real `run_formatters`, so `format_code = false` means no formatter call. Setup in each:
  `tmp_path` project with `pyproject.toml` containing `[tool.mcp-coder]\nformat_code = false`,
  patch the wrapper `mcp_coder.workflow_steps.commit.run_format_code`, leave `run_formatters`
  unpatched; assert the wrapper is not called.
  - Review (**new** `tests/workflows/review/test_core_formatter_preflight.py` — not
    `test_core_after_steps.py`, which is at 736/750): restore the real `run_formatters` over the review conftest
    mock (`monkeypatch.setattr(core, "run_formatters", commit.run_formatters)`) and drive a round
    that reaches the formatting call (`review/core.py:468`).
  - fix-ci (`tests/workflows/fix_ci/test_core.py`) and `check_branch_status --fix`
    (`tests/cli/commands/test_check_branch_status_auto_fixes.py`): both format via
    `check_and_fix_ci` → `workflow_steps.ci.run_formatters`; drive `check_and_fix_ci` far enough
    to reach that call (mock CI status / LLM as the existing `tests/workflow_steps/test_ci_check_and_fix.py`
    tests do), without patching `mcp_coder.workflow_steps.ci.run_formatters`.
  - Put each test in the listed file (steps 4–6 extend the same files with pre-flight tests).
