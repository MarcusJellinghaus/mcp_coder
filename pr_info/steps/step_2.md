# Step 2 — Extract `TestStatusAssessmentConsumer`

> Prompt: Implement Step 2 of `pr_info/steps/summary.md` (#438). Mechanical,
> test-only move — no logic changes. Move the `TestStatusAssessmentConsumer`
> class out of `tests/workflows/vscodeclaude/test_status_display.py` into a new
> file `tests/workflows/vscodeclaude/test_status_display_assessment_consumer.py`.
> Keep the full suite green. Produce exactly one commit.

## WHERE

- Create `tests/workflows/vscodeclaude/test_status_display_assessment_consumer.py`.
- Modify `tests/workflows/vscodeclaude/test_status_display.py` (delete the class).

## WHAT

Move `TestStatusAssessmentConsumer` (original lines ~2033–2176) verbatim.

## HOW

1. New file starts with a one-line module docstring, then the **full copied
   import header** from `summary.md`, plus
   `from tests.workflows.vscodeclaude.conftest import _build_assessment`.
2. Paste the class body unchanged.
3. Delete the class from `test_status_display.py`.
4. Run `run_ruff_fix(select=["F401"])` to prune unused imports in both files.
   `mock_status_checks` (if used) auto-injects from conftest — do not import it.

## ALGORITHM

```
create new file: docstring + full header + `_build_assessment` import
paste TestStatusAssessmentConsumer verbatim
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
