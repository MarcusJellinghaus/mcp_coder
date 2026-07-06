# Step 7 — Extract `TestScenarioACrossModule`, drop allowlist entry, final verify

> Prompt: Implement Step 7 (final) of `pr_info/steps/summary.md` (#438).
> Mechanical, test-only move — no logic changes. Move `TestScenarioACrossModule`
> into a new file, which leaves the kept `test_status_display.py` holding only
> `TestStatusDisplay` and under 750 lines. In the **same commit**, remove the
> `test_status_display.py` entry from `.large-files-allowlist` and run the full
> verification. Produce exactly one commit.

## WHERE

- Create `tests/workflows/vscodeclaude/test_status_display_scenario.py`.
- Modify `tests/workflows/vscodeclaude/test_status_display.py` (delete the
  class; leaves only `TestStatusDisplay`, ~470 lines).
- Modify `.large-files-allowlist` (remove the
  `tests/workflows/vscodeclaude/test_status_display.py` line).

## WHAT

Move `TestScenarioACrossModule` (original lines ~1890–2032) verbatim.

## HOW

1. New file: one-line docstring + **full copied import header** +
   `from tests.workflows.vscodeclaude.conftest import _build_assessment`.
2. Paste the class body unchanged.
3. Delete the class from `test_status_display.py`.
4. `run_ruff_fix(select=["F401"])` prunes unused imports across all touched
   files (including the now-final kept file).
5. Remove the `.large-files-allowlist` line for
   `tests/workflows/vscodeclaude/test_status_display.py`. This is done in this
   commit because the kept file only now drops under 750 — no premature removal,
   no under-limit-but-allowlisted window.

## ALGORITHM

```
create new file: docstring + full header + `_build_assessment` import
paste TestScenarioACrossModule verbatim
remove the class from test_status_display.py
ruff_fix(select=["F401"]) across touched files
delete the allowlist line for test_status_display.py
```

## DATA

No data-structure changes. Test-class relocation + allowlist edit only.

## Definition of done (closure gating)

- `mcp__mcp-workspace__check_file_size` reports **all** resulting files under 750
  and **no stale allowlist entry**.
- `.large-files-allowlist` no longer lists `test_status_display.py`.
- `mcp-coder git-tool compact-diff` across the whole branch shows **only** import
  changes and new/deleted file headers — proving the mechanical-move guarantee.

## Checks (must pass → one commit)

`run_format_code`, `run_ruff_fix(select=["F401"])`, `run_lint_imports_check`,
`run_vulture_check`,
`run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`,
`run_pylint_check`, `run_mypy_check`, plus `check_file_size` and `compact-diff`
as above.
