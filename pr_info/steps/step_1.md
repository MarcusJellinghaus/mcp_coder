# Step 1 — Replace the `branch_status` fork with a shim; delete dead code

**One commit:** shim + dead-code deletion + check-test churn are one atomic
refactor (you cannot delete `ci_log_parser.py` without the shim replacing the
fork that imports it, and the fork-internal tests die with the fork).

## WHERE

- Rewrite: `src/mcp_coder/checks/branch_status.py`
- Delete: `src/mcp_coder/checks/ci_log_parser.py`
- Delete: `tests/checks/test_ci_log_parser.py`
- Delete: `tests/checks/test_branch_status_pr_fields.py`
- Delete + recreate (small): `tests/checks/test_branch_status.py`
- Verify unchanged (imports must still resolve through the shim):
  `src/mcp_coder/checks/__init__.py`, `src/mcp_coder/__init__.py`,
  `src/mcp_coder/workflow_steps/ci.py`

## WHAT

`checks/branch_status.py` becomes a pure re-export module — no logic, no
dataclass definitions. Re-export **only** these names, from their real homes:

```python
"""Thin shim re-exporting branch-status from mcp_workspace.

The fork was collapsed onto mcp_workspace.checks.* (issue #1068). Only names
actually consumed by mcp-coder callers/tests are re-exported. collect_pr_feedback
is intentionally NOT re-exported — consumers reach PR feedback transitively via
collect_branch_status's report fields.
"""
from typing import List

from mcp_workspace.checks.branch_status import (
    BranchStatusReport,
    collect_branch_status,
    create_empty_report,
    get_failed_jobs_summary,
)
from mcp_workspace.checks.branch_status_rendering import CIStatus, GITHUB_TOKEN_HINT

__all__: List[str] = [
    "BranchStatusReport",
    "collect_branch_status",
    "create_empty_report",
    "get_failed_jobs_summary",
    "CIStatus",
    "GITHUB_TOKEN_HINT",
]
```

## HOW (integration points)

- `checks/__init__.py` imports `collect_branch_status` from `.branch_status` —
  keeps working via the shim (no edit).
- `src/mcp_coder/__init__.py:37` re-exports `collect_branch_status` — keeps
  working (no edit).
- `workflow_steps/ci.py:17` imports `get_failed_jobs_summary` from
  `mcp_coder.checks.branch_status` — keeps working (no edit).
- `cli/commands/check_branch_status.py` imports `GITHUB_TOKEN_HINT`,
  `BranchStatusReport`, `CIStatus`, `collect_branch_status` — all re-exported.
  (Its behavior is updated in Step 2, not here.)
- Confirm nothing else in `src/` imports `mcp_coder.checks.ci_log_parser`
  (grep first). It is imported only by the old fork.

## ALGORITHM

None — this step removes logic rather than adding it. The upstream package owns
PR discovery, merge override, PR-feedback collection, and rendering.

## DATA

`BranchStatusReport` (upstream) now carries the extra fields
`pr_mergeable`, `pr_mergeable_state`, `pr_feedback_text`,
`pr_feedback_blocks_merge`, `pr_feedback_undeterminable` (all with defaults).
`CIStatus` gains `UNAVAILABLE` and `UNKNOWN` members. Existing callers that
construct `BranchStatusReport(...)` with only the original required fields stay
valid (new fields default).

## TESTS (TDD — write/adjust first, then delete the fork)

New `tests/checks/test_branch_status.py` (small — shim contract only):
- `test_shim_reexports_expected_names` — import each name in `__all__`; assert
  callable/class as appropriate.
- `test_ci_status_has_degradation_members` — assert `CIStatus.UNAVAILABLE` and
  `CIStatus.UNKNOWN` exist (proves #244 is present).
- `test_report_has_pr_feedback_fields` — assert `BranchStatusReport` dataclass
  fields include `pr_feedback_text`, `pr_feedback_blocks_merge`,
  `pr_feedback_undeterminable`.
- `test_collect_pr_feedback_not_reexported` — assert
  `not hasattr(mcp_coder.checks.branch_status, "collect_pr_feedback")`.

Do **not** re-test upstream internals (`_build_ci_error_details`,
`_generate_recommendations` wording, exact formatter output) — mcp-workspace's
own suite covers them.

**Incidental fallout:** running the full suite may reveal a few existing CLI
tests that asserted the *old* fork's exact `format_for_human` text. Fix only
those by relaxing to behavioral assertions (exit code / that output was
printed); do not add new behavior here.

## CHECKS

`grep` for `ci_log_parser` and `test_branch_status_pr_fields` leftovers, then:
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`
- `mcp__tools-py__run_mypy_check`

## LLM PROMPT

> Implement **Step 1** of `pr_info/steps/summary.md` (issue #1068): replace the
> diverged `src/mcp_coder/checks/branch_status.py` fork with a thin shim and
> remove the dead code it pinned.
>
> First verify the prerequisite from the summary:
> `python -c "from mcp_workspace.checks.branch_status_rendering import CIStatus, GITHUB_TOKEN_HINT; CIStatus.UNKNOWN"`
> must succeed. If it fails, STOP and report that the venv lacks mcp-workspace #244.
>
> Then, exactly as specified in `pr_info/steps/step_1.md`:
> 1. Rewrite `checks/branch_status.py` as a re-export of `BranchStatusReport`,
>    `collect_branch_status`, `create_empty_report`, `get_failed_jobs_summary`
>    (from `mcp_workspace.checks.branch_status`) and `CIStatus`,
>    `GITHUB_TOKEN_HINT` (from `mcp_workspace.checks.branch_status_rendering`).
>    Do NOT re-export `collect_pr_feedback`.
> 2. Delete `checks/ci_log_parser.py`, `tests/checks/test_ci_log_parser.py`, and
>    `tests/checks/test_branch_status_pr_fields.py`.
> 3. Delete and recreate `tests/checks/test_branch_status.py` with the small
>    shim-contract tests listed in the step.
> 4. Confirm `checks/__init__.py`, `src/mcp_coder/__init__.py`, and
>    `workflow_steps/ci.py` still import cleanly through the shim (no edits
>    expected). Fix any incidental CLI test that asserted the old fork's exact
>    formatter text by relaxing it to a behavioral assertion.
>
> Use MCP tools only. Run pylint, pytest (parallel, unit-only exclusions), and
> mypy; all must pass. Produce exactly one commit.
