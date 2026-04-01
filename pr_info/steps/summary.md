# Summary: `--wait-for-pr` flag for `check branch-status`

## Issue
**#620** — Add `--wait-for-pr` to `mcp-coder check branch-status` that polls for PR creation, then proceeds with normal branch-status check (including CI).

## Architecture / Design Changes

### New Capability: PR Discovery Phase
The `check branch-status` command gains an optional **PR discovery phase** that runs *before* the existing CI-wait + status-collection flow. When `--wait-for-pr` is set:

1. **Guard**: Verify remote tracking branch exists (prevents useless 600s wait)
2. **Poll**: Query GitHub API for open PR matching current branch as `head`
3. **Proceed**: Once PR found, run existing branch-status flow unchanged

### Key Design Decisions
- **No changes to CI querying** — `get_latest_ci_status(branch)` already captures PR-triggered workflows
- **Separate timeouts** — `--pr-timeout` (PR discovery) vs `--ci-timeout` (CI polling) are independent
- **Simple inline polling** — No new abstractions; PR polling is a while loop in one place
- **Reuse existing types** — `find_pull_request_by_head()` returns `List[PullRequestData]`

### Data Model Change
`BranchStatusReport` (frozen dataclass) gains three optional fields:
- `pr_number: Optional[int] = None`
- `pr_url: Optional[str] = None`
- `pr_found: Optional[bool] = None`

These are populated by the caller (command layer), not by `collect_branch_status()`.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Add `find_pull_request_by_head()` method |
| `src/mcp_coder/cli/parsers.py` | Add `--wait-for-pr` and `--pr-timeout` arguments |
| `src/mcp_coder/checks/branch_status.py` | Extend `BranchStatusReport` with PR fields + display |
| `src/mcp_coder/cli/commands/check_branch_status.py` | PR discovery polling, remote guard, CI pending hint |
| `.claude/skills/check_branch_status/SKILL.md` | Document new flags |
| `src/mcp_coder/utils/git_operations/branch_queries.py` | Add `has_remote_tracking_branch()` helper |
| `.claude/skills/implementation_approve/SKILL.md` | Gate on `--wait-for-pr` branch-status check |

## Files Created (Tests)

| File | Purpose |
|------|---------|
| `tests/utils/github_operations/test_pr_manager_find_by_head.py` | Tests for `find_pull_request_by_head()` |
| `tests/cli/commands/test_check_branch_status_pr_waiting.py` | Tests for PR discovery polling, remote guard, CI hint |
| `tests/checks/test_branch_status_pr_fields.py` | Tests for PR fields in `BranchStatusReport` |

## Files NOT Changed
- `src/mcp_coder/utils/github_operations/ci_results_manager.py` — existing `get_latest_ci_status(branch)` already captures PR-triggered workflows
