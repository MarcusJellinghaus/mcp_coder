# Step 3 — Move group B (`TestProcessEligibleIssuesMaxSessions`) to `test_session_launch_process_issues.py`

## LLM prompt
> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_3.md`) exactly.
> This is a pure refactoring: move the class with `move_symbol` (dry run first). The destination's import block must end up unchanged.
> Use MCP tools only. Finish with the standard checks from the summary, then make one commit.

## WHERE
- Source: `tests/workflows/vscodeclaude/test_session_restart.py`
- Destination: `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` (existing, 6 tests). It already has `TestProcessEligibleIssuesBranchRequirement` and `TestProcessEligibleIssuesPrefetchedIssues`.

## WHAT
- `mcp__mcp-tools-py__move_symbol(source_file=".../test_session_restart.py", symbol_names=["TestProcessEligibleIssuesMaxSessions"], dest_file=".../test_session_launch_process_issues.py")`
- The class holds 1 test: `test_process_eligible_issues_respects_max_sessions`. It uses only `process_eligible_issues`.

## HOW
- **Destination:** it already imports `process_eligible_issues`, so its import block must stay unchanged. If rope added a duplicate import line (`F811`), delete only the added line.
- **Source:** remove imports that are now unused (for example `process_eligible_issues`), using ruff as described in the summary.
- **Class position:** where rope places the class doesn't matter. Don't reorder by hand.

## ALGORITHM
```
move_symbol dry run -> must list only the source and the destination file
move_symbol (real)
destination imports unchanged; source F401 cleaned
run_format_code
gate: pytest -v destination -> 7 passed; directory collect -> 688
standard checks; commit
```

## DATA / gates
- **Dry run** touches files other than the two named → write one line to `pr_info/.blocked.txt` and stop.
- **`run_pytest_check(extra_args=["-v", "tests/workflows/vscodeclaude/test_session_launch_process_issues.py"])`** → **7 passed**.
- **`run_pytest_check(extra_args=["-v", "tests/workflows/vscodeclaude/test_session_restart.py"])`** → **12 passed**.
- **Directory collect-only** → **688**.
- **Compact diff:** the moved block (suppressed) and import removals in the source only. Nothing changes in the destination's import block. On any gate failure: move the class back with `move_symbol`, write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(vscodeclaude): move max_sessions test to test_session_launch_process_issues.py`
