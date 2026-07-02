# Step 3 — CLI integration: guard `--wait-for-pr`, gate the `--ci-timeout` wait, consistent exit code `2`

> Read `pr_info/steps/summary.md` first. Depends on Steps 1 and 2. This step makes the
> CLI degrade gracefully (no silent exit `2` from the `--wait-for-pr` or CI-wait paths
> before printing) and return a distinct, consistent exit code `2` for the missing-token
> case on **all** paths — read-only, `--ci-timeout`, `--wait-for-pr`, and `--fix`.

## WHERE
- Source: `src/mcp_coder/cli/commands/check_branch_status.py`
  (function `execute_check_branch_status`)
- Tests:  `tests/cli/commands/test_check_branch_status.py`

## WHAT

### 3a. Imports
Extend the existing shim import with `get_github_token`:
```python
from ...mcp_workspace_github import (
    CIResultsManager,
    CIStatusData,
    PullRequestManager,
    get_github_token,
)
```
And extend the existing `...checks.branch_status` import with `GITHUB_TOKEN_HINT` (the
constant introduced in Step 1) — it is used by the `--wait-for-pr` guard in 3b:
```python
from ...checks.branch_status import (
    BranchStatusReport,
    CIStatus,
    GITHUB_TOKEN_HINT,
    collect_branch_status,
)
```

### 3b. Guard the `--wait-for-pr` path (Q2 decision)
The `--wait-for-pr` block runs early in `execute_check_branch_status` (inside the
`if getattr(args, "wait_for_pr", False):` block) and constructs
`pr_manager = PullRequestManager(project_dir)`. On a missing token that constructor raises
"GitHub token not found", which today is swallowed by the **outer** `except` and returns
exit `2` **without printing anything** — a silent failure.

Decision: `--wait-for-pr` must still FAIL with exit `2` when the token is missing (it
genuinely cannot check CI), but it must fail **cleanly** with the actionable hint. Add a
proactive guard **at the very top of the `--wait-for-pr` block**, before the
`has_remote_tracking_branch` guard and before `PullRequestManager(project_dir)` is
constructed:
```python
if getattr(args, "wait_for_pr", False):
    if get_github_token() is None:
        # Proactive: --wait-for-pr cannot check CI without a token. Fail cleanly
        # with the actionable hint instead of letting PullRequestManager raise into
        # the silent outer except.
        print(f"CI Status: \U0001F512 UNAVAILABLE — {GITHUB_TOKEN_HINT}")
        return 2
    # ... existing remote-tracking guard + PullRequestManager(project_dir) ...
```
Import `GITHUB_TOKEN_HINT` alongside the other `branch_status` imports (see 3a). Use the
same `print(...)` sink the report uses (stdout), so the hint is visible regardless of log
routing. Detection stays proactive (`get_github_token() is None`) — never match on the
exception text/type.

### 3c. Gate the CI-wait block
The `--ci-timeout` wait constructs `CIResultsManager`, which raises (→ `return 2`) when no
token, *before* the report is printed. Add one condition so the wait is skipped when no
token, falling through to the partial report:
```python
# was: if args.ci_timeout > 0:
if args.ci_timeout > 0 and get_github_token() is not None:
    ...
```
(Optional: `logger.debug("Skipping CI wait — no GitHub token")` in the skipped case.)

### 3d. Centralized exit code — hoisted above `--fix` (Q1 decision)
The `UNAVAILABLE → return 2` check must run on **all** paths. If it lived only in the
no-fix exit branch, `--fix` + no token would slip through: `_run_auto_fixes` sees
`UNAVAILABLE != FAILED`, treats it as "nothing to fix", returns `True`, and the command
returns `0` before ever reaching the no-fix exit logic.

Fix: hoist the `UNAVAILABLE` check to run **immediately after the report is printed** and
**before** the `if args.fix > 0:` block, so a missing token returns exit `2` on the
read-only, `--ci-timeout`, and `--fix` paths alike:
```python
# ... after print(output) (and the CI-pending hint), BEFORE `if args.fix > 0:` ...
if report.ci_status == CIStatus.UNAVAILABLE:
    return 2  # auth missing — CI truth unknown; nothing to fix
```
The existing no-fix `FAILED → 1 / else 0` logic stays where it is (it is only reached when
the token is present, so it needs no `UNAVAILABLE` case):
```python
if report.ci_status == CIStatus.FAILED:
    return 1
return 0
```

## HOW (integration points)
- No change to `collect_branch_status` — the state was set in Step 2; this step only reads
  `report.ci_status`.
- The partial report (rebase + tasks) is `print()`ed *before* the hoisted exit-`2` return,
  so exit `2` loses no information on the read-only / `--ci-timeout` / `--fix` paths.
- The `--wait-for-pr` guard returns *before* the report is collected (the PR wait happens
  early), so it prints the hint line directly (3b) rather than a full report.
- `CIStatus` is already imported in this module; `GITHUB_TOKEN_HINT` is added in 3a.

## ALGORITHM (pseudocode for the command flow)
```
if args.wait_for_pr:
    if get_github_token() is None:
        print("CI Status: 🔒 UNAVAILABLE — " + GITHUB_TOKEN_HINT)
        return 2                # clean fail, no silent PullRequestManager raise
    ... existing remote-tracking guard + PR wait ...
if ci_timeout > 0 and get_github_token() is not None:
    wait_for_ci(...)            # skipped entirely when token missing
report = collect_branch_status(project_dir)
print(report.format_*())        # carries the 🔒 hint from Step 1
if report.ci_status == UNAVAILABLE: return 2   # HOISTED: runs before the --fix block
if args.fix > 0:
    ... run auto-fixes ...      # unreachable on missing token now
    return 0 or 1
if report.ci_status == FAILED:  return 1
return 0
```

## DATA
- Missing token, no `--fix`: prints partial report (with hint), returns `2`.
- Missing token, `--ci-timeout 60`: wait is skipped (no raise), partial report printed,
  returns `2`.
- Missing token, `--fix N`: hoisted check returns `2` before auto-fixes run (previously
  `_run_auto_fixes` treated `UNAVAILABLE` as "nothing to fix" and returned `0`).
- Missing token, `--wait-for-pr`: prints the hint line, returns `2` (previously silent
  exit `2` with no output).
- Token present: behavior unchanged on every path.

## TESTS (write first — TDD)
Add to `tests/cli/commands/test_check_branch_status.py` (patch
`mcp_coder.cli.commands.check_branch_status.get_github_token`):
1. Missing token (`get_github_token() → None`), `ci_timeout=0`, `fix=0`:
   `execute_check_branch_status` returns `2`; captured stdout contains the hint
   (`UNAVAILABLE` / "GitHub token"). Use a `collect_branch_status` mock returning an
   `UNAVAILABLE` report, or let it flow through.
2. Missing token with `ci_timeout > 0`: `_wait_for_ci_completion` / `CIResultsManager` is
   **not** called (assert via mock), report still printed, returns `2`.
3. **`--fix` + no token → exit 2 (Q1):** `get_github_token() → None`, `fix=1` (or more),
   `collect_branch_status` mock returns an `UNAVAILABLE` report. Assert the return is `2`
   and that the auto-fix path did not run (e.g. patch `_run_auto_fixes` / `check_and_fix_ci`
   and assert it was **not** called) — proving the hoisted check short-circuits before
   `--fix`.
4. **`--wait-for-pr` + no token → hint + exit 2 (Q2):** `get_github_token() → None`,
   `wait_for_pr=True` (set `pr_timeout` too, e.g. `0`). Assert the return is `2`, captured
   stdout contains the `GITHUB_TOKEN_HINT` text, and `PullRequestManager` was **not**
   constructed (patch it and assert not called) — proving the proactive guard fires before
   the silent outer except.
5. Token present: existing tests unchanged (patch `get_github_token` to return a token in
   any test that exercises the wait / `--wait-for-pr` path so the guards stay open).

## COMMIT
Single commit: `--wait-for-pr` guard + CI-wait gate + hoisted exit code + tests, all checks
green.

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
> the shim and `GITHUB_TOKEN_HINT` from `...checks.branch_status`. (a) At the top of the
> `--wait-for-pr` block, before the remote-tracking guard and before
> `PullRequestManager(project_dir)`, add `if get_github_token() is None:` → print
> `f"CI Status: \U0001F512 UNAVAILABLE — {GITHUB_TOKEN_HINT}"` and `return 2`. (b) Change
> the CI-wait guard to `if args.ci_timeout > 0 and get_github_token() is not None:`.
> (c) Hoist `if report.ci_status == CIStatus.UNAVAILABLE: return 2` to run immediately
> after the report is printed and **before** the `if args.fix > 0:` block (leave the no-fix
> `FAILED → 1 / else 0` logic as-is). Follow TDD: add the tests in Step 3 first (patching
> `mcp_coder.cli.commands.check_branch_status.get_github_token`), including the `--fix` +
> no-token → exit 2 and `--wait-for-pr` + no-token → hint + exit 2 cases; then implement;
> ensure existing wait-path tests patch the token open. Detection stays proactive
> (`get_github_token()`), never exception/string matching. Use only MCP tools per
> CLAUDE.md, run pylint/pytest/mypy, and produce exactly one commit.
