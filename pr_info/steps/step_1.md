# Step 1 — Relocate the existing PR-health tests (pure move)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> This step only moves existing tests into new files; do not change any source code
> under `src/` and do not change test behaviour. Run pylint, pytest (fast unit tests,
> `-n auto`) and mypy; all must pass. Format, then make exactly one commit.

## Goal

Make step 2's diff reviewable: the PR-health tests already live in the files they will
end up in, so step 2 shows only real rewrites. No source change, no behaviour change.

## WHERE

- Create `tests/workflows/vscodeclaude/test_checks.py`
- Create `tests/workflows/vscodeclaude/test_checks_review_comments.py`
- Modify `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`
- Delete `tests/workflows/vscodeclaude/test_session_launch_review_comments.py`
- Modify `.large-files-allowlist`

## WHAT

1. **`test_checks.py`** — move verbatim from `test_session_launch_process_issues.py`:
   - `MOCK_MERGE_CONFLICT_LABELS_CONFIG`, `MOCK_CI_LABELS_CONFIG`
   - `class TestProcessEligibleIssuesMergeConflictDetection` (incl. `_make_pr_issue`, `_setup_common_mocks`)
   - `class TestProcessEligibleIssuesCIDetection`
   - Module docstring: `"""Tests for PR-health checks on status-10 issues (checks.py)."""`
   - Imports only what the moved code uses (`Any`, `MagicMock`, `pytest`, `IssueData`,
     `process_eligible_issues` from `mcp_coder.workflows.vscodeclaude.session_launch`).
2. **`test_checks_review_comments.py`** — the full content of
   `test_session_launch_review_comments.py`, with:
   - the relative import changed from `.test_session_launch_process_issues` to `.test_checks`
   - docstring: `"""Tests for review-comment detection in checks.py."""`
3. **`test_session_launch_process_issues.py`** — keeps only
   `TestProcessEligibleIssuesBranchRequirement` and `TestProcessEligibleIssuesPrefetchedIssues`.
   Remove imports that become unused (e.g. `logging`, `Any`) — let pylint/ruff tell you.
4. Delete `test_session_launch_review_comments.py`.
5. `.large-files-allowlist`: remove the line
   `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` if the file is now
   ≤ 750 lines (expected: ~495). Verify with `mcp__mcp-workspace__check_file_size(max_lines=750)`.

## HOW

- Pure cut-and-paste; keep test names, bodies and patch paths unchanged.
- Patch paths still point at `session_launch.*` / `checks._build_pr_manager` — that is correct for this step.

## ALGORITHM

None (relocation only).

## DATA

None.

## Verification

- Same number of tests collected as before the move (sum across the files).
- pylint, pytest, mypy pass; `check_file_size(max_lines=750)` lists none of the touched test files
  unless they are on the allowlist.

## Commit

`test(vscodeclaude): move PR-health tests into test_checks modules (#1238)`
