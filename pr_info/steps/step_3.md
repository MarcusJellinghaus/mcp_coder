# Step 3 — CLI integration: gate the `--ci-timeout` wait + exit code `2`

> Read `pr_info/steps/summary.md` first. Depends on Steps 1 and 2. This step makes the
> CLI degrade gracefully (no exit `2` from the wait path before printing) and return a
> distinct exit code for the missing-token case.

## WHERE
- Source: `src/mcp_coder/cli/commands/check_branch_status.py`
  (function `execute_check_branch_status`)
- Tests:  `tests/cli/commands/test_check_branch_status.py`

## WHAT

### 3a. Import `get_github_token`
Extend the existing shim import:
```python
from ...mcp_workspace_github import (
    CIResultsManager,
    CIStatusData,
    PullRequestManager,
    get_github_token,
)
```

### 3b. Gate the CI-wait block
The `--ci-timeout` wait constructs `CIResultsManager`, which raises (→ `return 2`) when no
token, *before* the report is printed. Add one condition so the wait is skipped when no
token, falling through to the partial report:
```python
# was: if args.ci_timeout > 0:
if args.ci_timeout > 0 and get_github_token() is not None:
    ...
```
(Optional: `logger.debug("Skipping CI wait — no GitHub token")` in the skipped case.)

### 3c. Centralized exit code
At the existing final exit logic (after the report is printed, in the no-fix branch), add
the `UNAVAILABLE` case **before** the `FAILED` case:
```python
if report.ci_status == CIStatus.UNAVAILABLE:
    return 2  # auth missing — CI truth unknown
if report.ci_status == CIStatus.FAILED:
    return 1
return 0
```

## HOW (integration points)
- No change to `collect_branch_status` — the state was set in Step 2; this step only reads
  `report.ci_status`.
- The partial report (rebase + tasks) is `print()`ed *before* the return, so exit `2`
  loses no information.
- `CIStatus` is already imported in this module.

## ALGORITHM (pseudocode for the command flow)
```
if ci_timeout > 0 and get_github_token() is not None:
    wait_for_ci(...)            # skipped entirely when token missing
report = collect_branch_status(project_dir)
print(report.format_*())       # carries the 🔒 hint from Step 1
if report.ci_status == UNAVAILABLE: return 2
if report.ci_status == FAILED:      return 1
return 0
```

## DATA
- Missing token, no `--fix`: prints partial report (with hint), returns `2`.
- Missing token, `--ci-timeout 60`: wait is skipped (no raise), partial report printed,
  returns `2`.
- Token present: behavior unchanged.

## TESTS (write first — TDD)
Add to `tests/cli/commands/test_check_branch_status.py` (patch
`mcp_coder.cli.commands.check_branch_status.get_github_token`):
1. Missing token (`get_github_token() → None`), `ci_timeout=0`: `execute_check_branch_status`
   returns `2`; captured stdout contains the hint (`UNAVAILABLE` / "GitHub token"). Use a
   `collect_branch_status` mock returning an `UNAVAILABLE` report, or let it flow through.
2. Missing token with `ci_timeout > 0`: `_wait_for_ci_completion` / `CIResultsManager` is
   **not** called (assert via mock), report still printed, returns `2`.
3. Token present: existing tests unchanged (patch `get_github_token` to return a token in
   any test that exercises the wait path so the gate stays open).

## COMMIT
Single commit: CLI gate + exit code + tests, all checks green.

## QUALITY GATES
```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check (extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```
Run `./tools/format_all.sh` before committing.

## LLM PROMPT
> Implement Step 3 from `pr_info/steps/step_3.md` (context in `pr_info/steps/summary.md`).
> In `src/mcp_coder/cli/commands/check_branch_status.py`: import `get_github_token` from
> the shim; change the CI-wait guard to
> `if args.ci_timeout > 0 and get_github_token() is not None:`; and add
> `if report.ci_status == CIStatus.UNAVAILABLE: return 2` immediately before the existing
> `FAILED → return 1` in the no-fix exit logic. Follow TDD: add the tests in Step 3 first
> (patching `mcp_coder.cli.commands.check_branch_status.get_github_token`), then implement;
> ensure existing wait-path tests patch the token open. Use only MCP tools per CLAUDE.md,
> run pylint/pytest/mypy, and produce exactly one commit.
