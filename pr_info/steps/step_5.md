# Step 5 — Extract `TestDisplayStatusTableBranchIndicators`

> Prompt: Implement Step 5 of `pr_info/steps/summary.md` (#438). Mechanical,
> test-only move — no logic changes. Move
> `TestDisplayStatusTableBranchIndicators` out of
> `tests/workflows/vscodeclaude/test_status_display.py` into a new file
> `tests/workflows/vscodeclaude/test_status_display_branch_indicators.py`. Keep
> the full suite green. Produce exactly one commit.

## WHERE

- Create `tests/workflows/vscodeclaude/test_status_display_branch_indicators.py`.
- Modify `tests/workflows/vscodeclaude/test_status_display.py` (delete the class).

## WHAT

Move `TestDisplayStatusTableBranchIndicators` (original lines ~1506–1755)
verbatim.

## HOW

1. New file: one-line docstring + **full copied import header** +
   `from tests.workflows.vscodeclaude.conftest import _build_assessment`.
2. Paste the class body unchanged.
3. Delete the class from `test_status_display.py`.
4. `run_ruff_fix(select=["F401"])` prunes unused imports in both files.
   `mock_status_checks` auto-injects from conftest — do not import it.

## ALGORITHM

```
create new file: docstring + full header + `_build_assessment` import
paste TestDisplayStatusTableBranchIndicators verbatim
remove the class from test_status_display.py
ruff_fix(select=["F401"]) on both files
```

## DATA

No data-structure changes. Test-class relocation only.

## Checks (must pass → one commit)

`run_format_code`, `run_ruff_fix(select=["F401"])`, `run_lint_imports_check`,
`run_vulture_check`,
`run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`,
`run_pylint_check`, `run_mypy_check`. Confirm via `compact-diff` that only
imports + new/deleted file headers appear.
