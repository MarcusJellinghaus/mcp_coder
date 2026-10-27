# Step 2 — Replace the four identical local copies with `make_assessment`

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly. Step 1 is done: `make_assessment` exists in `tests/workflows/vscodeclaude/conftest.py`. This is a test-only refactor. Follow the summary's "Shared per-step check procedure". Produce exactly one commit.

## Precondition
`conftest.py` defines `def make_assessment(`. If it does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE
All in `tests/workflows/vscodeclaude/`:
- `test_session_restart_cache.py`
- `test_session_restart_closed_sessions.py`
- `test_session_restart_branch_integration.py`
- `test_closed_issues_integration.py`

## WHAT
- No new functions.
- Each file loses its module-level `def _make_assessment(...)`. Its body is identical to the conftest builder.

## HOW
In each file:
1. Delete the whole `def _make_assessment(...)` block, including its docstring.
2. Add `from tests.workflows.vscodeclaude.conftest import make_assessment` after the other imports, as a separate first-party import block. Keep the existing import order style; the formatter will sort it.
3. Run `edit_file(old_string="_make_assessment(", new_string="make_assessment(", replace_all=True)`. Leave the arguments unchanged.

After all four files are done, run `run_ruff_fix(select=["F401"], target_directories=["tests/workflows/vscodeclaude"])`. Then check the resulting `mcp_coder.workflows.vscodeclaude.types` imports:

| File | Expected `types` import after the fix |
|---|---|
| `test_session_restart_cache.py` | only `VSCodeClaudeSession` |
| `test_session_restart_closed_sessions.py` | no top-level import (the local import inside a test stays) |
| `test_session_restart_branch_integration.py` | no import |
| `test_closed_issues_integration.py` | unchanged; the two inline `SessionAssessment(...)` constructions still use every name |

Do not touch the inline `SessionAssessment(...)` constructions in `test_closed_issues_integration.py`.

## ALGORITHM
```
for file in four_files:
    delete local def _make_assessment block
    add conftest import of make_assessment
    replace "_make_assessment(" -> "make_assessment("
ruff fix F401 on tests/workflows/vscodeclaude
verify the types imports match the table
```

## DATA
- No data changes. Every call returns the same `SessionAssessment` as before.

## Done when
- `search_files(pattern="_make_assessment", glob="tests/workflows/vscodeclaude/test_session_restart_*.py")` → 0 hits.
- `search_files(pattern="_make_assessment", glob="tests/workflows/vscodeclaude/test_closed_issues_integration.py")` → 0 hits.
- The shared check procedure passes and the counts are unchanged.
- Commit: `test(vscodeclaude): use shared make_assessment in restart and closed-issue tests`
