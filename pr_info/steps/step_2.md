# Step 2 — Move `TestBuildEligibleIssuesPrefetched` to `test_issues_branch_check.py`

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Step 1 must be committed. This is a pure move: use `mcp__mcp-tools-py__move_symbol`
> (dry run first), never edit moved code by hand. Only import lines may be edited.
> Run the full check suite from the summary; all must pass. Produce exactly one commit.

## WHERE
- Source: `tests/cli/commands/coordinator/test_core.py`
- Destination (exists after step 1): `tests/workflows/vscodeclaude/test_issues_branch_check.py`

## WHAT
Move class `TestBuildEligibleIssuesPrefetched` (2 tests + `_make_issue` helper method, currently
lines 1173–1298) verbatim. It tests only
`mcp_coder.workflows.vscodeclaude.issues.build_eligible_issues_with_branch_check`.
No new functions or signatures.

## HOW
1. **Preconditions** — if any fails, write one line to `pr_info/.blocked.txt` and stop:
   - `tests/workflows/vscodeclaude/test_issues_branch_check.py` exists and contains
     `TestBuildEligibleIssuesWithBranchCheck`.
   - `tests/cli/commands/coordinator/test_core.py` contains `TestBuildEligibleIssuesPrefetched`
     (`list_symbols`). If a separate coordinator split already moved it, use its new source file
     instead; if it cannot be found anywhere, block.
2. **Baseline** (no marker filter; record in the commit message body):
   - `--collect-only -q tests/cli/commands/coordinator/test_core.py` → expect 52
   - `--collect-only -q tests/cli/commands/coordinator/` → expect 158
   - `--collect-only -q tests/workflows/vscodeclaude/` → expect 680
   - `run_pytest_check(extra_args=["tests/cli/commands/coordinator/test_core.py::TestBuildEligibleIssuesPrefetched", "-v"])` → 2 passed
3. `move_symbol(source_file="tests/cli/commands/coordinator/test_core.py", symbol_names=["TestBuildEligibleIssuesPrefetched"], dest_file="tests/workflows/vscodeclaude/test_issues_branch_check.py", dry_run=True)`.
   If the dry run touches any other file, write one line to `pr_info/.blocked.txt` and stop.
   Otherwise apply with `dry_run=False`. Do not reorder classes by hand.
4. **Verify the move kept method-local code verbatim:** both
   `from mcp_coder.workflows.vscodeclaude.issues import (build_eligible_issues_with_branch_check,)`
   blocks must still sit inside `test_prefetched_cache_skips_redundant_lookup` and
   `test_no_prefetch_falls_back_to_cache_lookup`. If `move_symbol` hoisted, dropped or rewrote
   either, revert the move, write one line to `pr_info/.blocked.txt` and stop.
5. Imports:
   - `test_issues_branch_check.py`: should need nothing new — `Mock`, `pytest`, `IssueData`,
     `make_issue_data` are already imported from step 1. Remove any duplicate import line
     `move_symbol` added. The method-local re-imports stay (pylint `W0404` is disabled).
     If ruff reports `F811` on them, write one line to `pr_info/.blocked.txt` and stop.
   - `coordinator/test_core.py`: imports **unchanged** (`IssueData`, `make_issue_data`, `Mock`,
     `pytest` are still used by remaining classes). No other edit.
6. Run the check suite from the summary, plus
   `run_pytest_check(extra_args=["tests/workflows/vscodeclaude/test_issues_branch_check.py::TestBuildEligibleIssuesPrefetched", "-v"])` → 2 passed.

## ALGORITHM
```
check preconditions, record baseline counts + run 2 tests at old location
dry-run move_symbol -> verify only 2 files touched
apply move_symbol; confirm method-local imports intact
dedupe module-level imports in destination only if needed
run checks + 2 tests at new location + compare collect counts
```

## DATA — expected results
- `--collect-only -q`: `test_issues_branch_check.py` 9, `test_issues.py` 40,
  `test_issues_branch_requirements.py` 5, `coordinator/test_core.py` 50,
  `tests/workflows/vscodeclaude/` 682, `tests/cli/commands/coordinator/` 156.
  Total across the three original files: 99 before and after.
- `test_issues_branch_check.py` ~530 lines; `coordinator/test_core.py` ~1172 lines, still allowlisted.
- Compact diff: `coordinator/test_core.py` shows no hunk outside the moved class (trailing blank
  lines only).

## Commit
`test(vscodeclaude): move TestBuildEligibleIssuesPrefetched next to branch-check tests (#1316)`
