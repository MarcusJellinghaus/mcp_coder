# Step 3: Add CLI arguments and PR discovery polling to command

## LLM Prompt
> Read `pr_info/steps/summary.md` for context. Implement Step 3: Add `--wait-for-pr` and `--pr-timeout` CLI arguments, then implement the PR discovery polling logic, remote tracking guard, and CI pending hint in `check_branch_status.py`. Write tests first (TDD), then implement. Run all code quality checks after.

## WHERE
- **Test**: `tests/cli/commands/test_check_branch_status_pr_waiting.py` (new file)
- **Parser**: `src/mcp_coder/cli/parsers.py`
- **Command**: `src/mcp_coder/cli/commands/check_branch_status.py`

## WHAT

### Parser changes (`parsers.py`):
```python
# Add to branch_status_parser in add_check_parsers():
branch_status_parser.add_argument(
    "--wait-for-pr",
    action="store_true",
    help="Wait for PR creation, then proceed with normal branch-status check",
)
branch_status_parser.add_argument(
    "--pr-timeout",
    type=_validate_pr_timeout,
    default=600,
    metavar="SECONDS",
    help="Max seconds to wait for PR to appear (default: 600)",
)
```

Add `_validate_pr_timeout` function (reuse pattern from `_validate_ci_timeout`).

### Command changes (`check_branch_status.py`):

New block in `execute_check_branch_status()`, before the existing CI-wait block:

```python
if args.wait_for_pr:
    # 1. Check remote tracking branch
    # 2. Poll for PR
    # 3. Store PR info for report
```

After report display, add CI pending hint:

```python
if args.ci_timeout == 0 and report.ci_status == "PENDING":
    print("CI pending. Use --ci-timeout to wait for completion.")
```

Pass PR fields when constructing report (replace `collect_branch_status` return with modified copy).

## HOW
- Import `PullRequestManager` and `has_remote_tracking_branch` from `mcp_coder.utils.git_operations.branch_queries` in check_branch_status.py
- Remote tracking check: Use existing `git_operations` utilities (e.g., add a `has_remote_tracking_branch(project_dir)` helper to `src/mcp_coder/utils/git_operations/branch_queries.py`) instead of raw `subprocess`. This is more testable and consistent with codebase patterns.
- PR polling: simple while loop with `time.sleep(20)` between iterations
- Use `dataclasses.replace()` to add PR fields to the frozen report returned by `collect_branch_status()`

## ALGORITHM (PR discovery in execute_check_branch_status)
```
1. If not args.wait_for_pr: skip to existing flow
2. Check remote tracking: call `has_remote_tracking_branch(project_dir)`
   - If False: print error message, return exit code 2
3. Create PullRequestManager(project_dir)
4. Poll loop (deadline = time.monotonic() + pr_timeout, loop while time.monotonic() < deadline):
   a. Call manager.find_pull_request_by_head(current_branch)
   b. If PRs found: store first PR's number/url, warn if multiple, break
   c. Sleep 20 seconds (only if time.monotonic() < deadline)
5. If no PR found after deadline: print timeout message, return exit code 1
6. After collect_branch_status(): use dataclasses.replace() to add pr_number, pr_url, pr_found
```

## ALGORITHM (CI pending hint)
```
1. After printing the report output
2. If args.ci_timeout == 0 and report.ci_status == CI_PENDING (import `CI_PENDING` from `branch_status.py`):
3. Print "CI pending. Use --ci-timeout to wait for completion."
```

## DATA
- `args.wait_for_pr: bool` (from CLI)
- `args.pr_timeout: int` (from CLI, default 600)
- PR info stored as local variables: `pr_number`, `pr_url`, `pr_found`
- Passed into report via `dataclasses.replace(report, pr_number=..., pr_url=..., pr_found=...)`

## TESTS (`test_check_branch_status_pr_waiting.py`)

### Parser tests:
| Test | Description |
|------|-------------|
| `test_wait_for_pr_flag_default` | Default is `False` |
| `test_wait_for_pr_flag_set` | `--wait-for-pr` sets to `True` |
| `test_pr_timeout_default` | Default is 600 |
| `test_pr_timeout_custom` | `--pr-timeout 300` sets to 300 |
| `test_pr_timeout_negative_rejected` | `--pr-timeout -1` raises error |

### `has_remote_tracking_branch` helper test:
| Test | Description |
|------|-------------|
| `test_has_remote_tracking_branch_true` | Branch with upstream returns True |
| `test_has_remote_tracking_branch_false` | Branch without upstream returns False |

### Remote tracking guard tests:
| Test | Description |
|------|-------------|
| `test_wait_for_pr_no_remote_tracking` | No upstream → exit code 2, error message |
| `test_wait_for_pr_with_remote_tracking` | Has upstream → proceeds to polling |

### PR polling tests:
| Test | Description |
|------|-------------|
| `test_wait_for_pr_found_immediately` | PR exists on first poll → proceeds, report has PR fields |
| `test_wait_for_pr_found_after_retries` | PR found on 2nd poll → correct behavior |
| `test_wait_for_pr_timeout` | No PR within timeout → exit code 1, timeout message |
| `test_wait_for_pr_multiple_prs_warning` | Multiple PRs → uses first, prints warning |

### CI pending hint test:
| Test | Description |
|------|-------------|
| `test_ci_pending_hint_when_timeout_zero` | CI pending + ci_timeout=0 → hint printed |
| `test_no_ci_hint_when_timeout_nonzero` | CI pending + ci_timeout>0 → no hint |
| `test_no_ci_hint_when_ci_passed` | CI passed + ci_timeout=0 → no hint |

### Existing behavior preservation:
| Test | Description |
|------|-------------|
| `test_no_wait_for_pr_skips_polling` | wait_for_pr=False → no PR manager created, normal flow, report.pr_found is None |

## STATUS MESSAGES
- "Branch '{branch}' has no remote tracking branch. Push first."
- "Waiting for PR creation on branch '{branch}' (timeout: {pr_timeout}s)..."
- "PR #{number} found ({url}). Proceeding with branch-status check."
- "Warning: Multiple PRs found for branch '{branch}'. Using PR #{number}."
- "No PR found for branch '{branch}' within timeout ({pr_timeout}s)."
- "CI pending. Use --ci-timeout to wait for completion."

## COMMIT
`feat(check_branch_status): add --wait-for-pr polling with remote guard and CI hint`
