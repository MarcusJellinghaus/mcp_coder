# Summary — Issue #1068: Branch status reads PR review feedback via dedup onto mcp-workspace

## Goal

Collapse the diverged `checks/branch_status.py` fork into a **thin shim** over the
upstream `mcp_workspace.checks.*` implementation (which now surfaces PR review
feedback, a three-state review gate, and missing-token / collection-failure
degradation), then wire the new feedback + gate into the **CLI** and the
**review workflows**. This is ~80% refactoring (fork → shim, delete divergent
code/tests) + ~20% new feature (`--fail-on-reviews` flag, review-workflow feed).

## Prerequisite (verify before starting)

The whole plan depends on upstream **mcp-workspace #244** being installed in the
venv. The shim and the exit contract import symbols that only exist in #244:

- `mcp_workspace.checks.branch_status_rendering` module
- `CIStatus.UNAVAILABLE` and `CIStatus.UNKNOWN`
- `GITHUB_TOKEN_HINT`
- `BranchStatusReport.pr_feedback_undeterminable`
- `collect_pr_feedback` returning a 3-tuple `(text, blocks_merge, undeterminable)`
- `create_empty_report(ci_status=…)`, `format_for_*(fail_on_reviews=…)`

**Verify first:** `python -c "from mcp_workspace.checks.branch_status_rendering import CIStatus, GITHUB_TOKEN_HINT; CIStatus.UNKNOWN"`
must succeed. If it fails, the venv holds the older #175 build — upgrade
`mcp_workspace` before implementing (do not proceed against #175).

## Architectural / design changes

1. **Fork → shim (one door).** `checks/branch_status.py` stops being a ~470-line
   parallel implementation and becomes a re-export module (the established
   `mcp_workspace_github.py` / `mcp_coder_utils.py` pattern). All branch-status
   logic — PR discovery, merge override, PR-feedback collection, rendering — now
   lives upstream and is covered by mcp-workspace's own suite. mcp-coder keeps a
   single seam.

2. **Re-export surface = only consumed names, sourced from their real homes.**
   `BranchStatusReport`, `collect_branch_status`, `create_empty_report`,
   `get_failed_jobs_summary` from `mcp_workspace.checks.branch_status`;
   `CIStatus`, `GITHUB_TOKEN_HINT` from `mcp_workspace.checks.branch_status_rendering`.
   `collect_pr_feedback` is **not** re-exported — no consumer calls it directly;
   its output reaches callers transitively through `collect_branch_status`'s
   report fields (`pr_feedback_text` / `pr_feedback_blocks_merge` /
   `pr_feedback_undeterminable`). One door, per the Goal.

3. **Dead code removed.** `checks/ci_log_parser.py` was imported only by the fork;
   it leaves with the fork (upstream owns `github_operations/ci_log_parser.py`).

4. **CLI: opt-in review gate + a pure exit-code contract.** A new
   `--fail-on-reviews` flag (default off = informational) both renders the
   `Review Gate:` header (via `format_*(fail_on_reviews=…)`) and drives the exit
   code through one pure helper `_exit_code(report, fail_on_reviews)` evaluated
   **2 → 1 → 0** (undeterminable wins over blocking wins over clean). The
   post-hoc `replace(report, pr_number=…)` enrichment is dropped — upstream
   `collect_branch_status` fills the PR fields itself. `--wait-for-pr` stays as a
   pure gate (block-until-PR, exit 1 on timeout).

5. **Review workflows see reviewer feedback (implementation lane only).** A new
   `ReviewConfig.thread_pr_feedback` flag (`True` for `review-implementation`,
   `False` for `review-plan`, mirroring the existing `inject_base_branch` /
   `run_after_steps` split) gates the feed. Each **implementation-lane** round
   calls `collect_branch_status(project_dir)` once (fresh, so resolved comments
   drop out) and threads `pr_feedback_text` (None-guarded) into **both** the
   fresh reviewer prompt (wrapped in a framing note so the reviewer treats
   comments as actionable findings) and the supervisor context (raw append). The
   **plan lane** skips the `collect_branch_status` GitHub call entirely.

### Exit-code contract (CLI) — evaluated in order

| Exit | Meaning | Triggers (first match wins) |
|------|---------|-----------------------------|
| **2** | Undeterminable | `CIStatus.UNAVAILABLE`, `CIStatus.UNKNOWN`, or `--fail-on-reviews` + `pr_feedback_undeterminable` |
| **1** | Determined & blocking | `CIStatus.FAILED`, or `--fail-on-reviews` + `pr_feedback_blocks_merge` |
| **0** | Proven clean | everything else |

### KISS decisions

- The two genuinely-new pieces of logic each collapse to **one small pure
  helper** (`_exit_code`, `_pr_feedback_note`) that is trivially unit-testable —
  this is where most of the test-churn savings come from.
- Obsolete check tests are **deleted and recreated small**, not rewritten in
  place.
- The reviewer PR-note reuses the **existing `ci_note` append seam** in
  `_run_reviewer` (a parallel `pr_note` kwarg), inventing no new plumbing.
- CLI passes `fail_on_reviews` to the formatter **unconditionally** (feedback
  renders by default; the flag only adds the gate header + exit code).

## Files / modules created or modified

### Modified (src)
- `src/mcp_coder/checks/branch_status.py` — replaced with shim (Step 1)
- `src/mcp_coder/cli/parsers.py` — add `--fail-on-reviews` (Step 2)
- `src/mcp_coder/cli/commands/check_branch_status.py` — `_exit_code` helper, drop
  `replace()` enrichment, pass `fail_on_reviews` to formatters (Step 2)
- `src/mcp_coder/workflows/review/config.py` — new `thread_pr_feedback` flag on
  `ReviewConfig` (Step 3)
- `src/mcp_coder/workflows/review/core.py` — per-round `collect_branch_status`
  (gated on `thread_pr_feedback`), `_pr_feedback_note` helper, thread into
  reviewer + supervisor (Step 3)
- `src/mcp_coder/workflows/review/reviewer.py` — new `pr_note` kwarg on
  `_run_reviewer` (Step 3)
- `docs/cli-reference.md` — `--fail-on-reviews` option + widened exit-code-2
  meaning (Step 2)

### Deleted (src)
- `src/mcp_coder/checks/ci_log_parser.py` (Step 1)

### Created / rewritten (tests)
- `tests/checks/test_branch_status.py` — deleted + recreated small: shim
  re-export assertions (Step 1)
- `tests/cli/commands/` — `_exit_code` contract table + `--fail-on-reviews`
  parser test (Step 2)
- `tests/workflows/review/test_reviewer.py` (`_run_reviewer` `pr_note` kwarg),
  `test_config.py` (new `thread_pr_feedback` flag), `test_core.py` (plan lane) +
  `test_core_after_steps.py` (implementation lane) — `_pr_feedback_note` unit +
  lane-gated core threading (Step 3)

### Deleted (tests)
- `tests/checks/test_ci_log_parser.py` (Step 1)
- `tests/checks/test_branch_status_pr_fields.py` (Step 1)

### Unchanged but verified still resolving through the shim
- `src/mcp_coder/checks/__init__.py` (re-exports `collect_branch_status`)
- `src/mcp_coder/__init__.py` (re-exports `collect_branch_status`)
- `src/mcp_coder/workflow_steps/ci.py` (imports `get_failed_jobs_summary`)

## Scope note

mcp-coder has **no** MCP tool for branch-status — only the CLI and the review
workflows. The "MCP tool parameter / server default" rows in the issue's
Decisions table are upstream (#244) concerns and are **out of scope** here.

## Steps

- **Step 1** — Shim `checks/branch_status.py`; delete `ci_log_parser.py` and its
  test; delete `test_branch_status_pr_fields.py`; recreate `test_branch_status.py`.
- **Step 2** — CLI: `--fail-on-reviews` flag + `_exit_code` contract + drop
  `replace()` enrichment + pass `fail_on_reviews` to formatters.
- **Step 3** — Review workflow (implementation lane only, via
  `ReviewConfig.thread_pr_feedback`): per-round `collect_branch_status`,
  `_pr_feedback_note` framing helper, thread into reviewer + supervisor; plan
  lane skips the GitHub call.
