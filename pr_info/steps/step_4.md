# Step 4 — Extract the delete-action classes

> Prompt: Implement Step 4 of `pr_info/steps/summary.md` (#438). Mechanical,
> test-only move — no logic changes. Move the three delete-action test classes
> out of `tests/workflows/vscodeclaude/test_status_display.py` into a new file
> `tests/workflows/vscodeclaude/test_status_display_delete_actions.py`. Keep the
> full suite green. Produce exactly one commit.

## WHERE

- Create `tests/workflows/vscodeclaude/test_status_display_delete_actions.py`.
- Modify `tests/workflows/vscodeclaude/test_status_display.py` (delete 3 classes).

## WHAT

Move verbatim, in original order (contiguous, lines ~921–1505):

- `TestBotStageSessionsDeleteAction` (~921–1243)
- `TestPrCreatedSessionsDeleteAction` (~1244–1415)
- `TestDisplayStatusTableSoftDelete` (~1416–1505)

## HOW

1. New file: one-line docstring + **full copied import header** +
   `from tests.workflows.vscodeclaude.conftest import _build_assessment`.
2. Paste the three classes unchanged, keeping their original order.
3. Delete all three from `test_status_display.py`.
4. `run_ruff_fix(select=["F401"])` prunes unused imports in both files.
   `mock_status_checks` auto-injects from conftest — do not import it.

## ALGORITHM

```
create new file: docstring + full header + `_build_assessment` import
paste the 3 delete-action classes verbatim (original order)
remove the 3 classes from test_status_display.py
ruff_fix(select=["F401"]) on both files
```

## DATA

No data-structure changes. Test-class relocation only. This is the largest
resulting file (~585 lines) — still comfortably under 750.

## Checks (must pass → one commit)

`run_format_code`, `run_ruff_fix(select=["F401"])`, `run_lint_imports_check`,
`run_vulture_check`,
`run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`,
`run_pylint_check`, `run_mypy_check`. Confirm via `compact-diff` that only
imports + new/deleted file headers appear.
