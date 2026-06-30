# Summary — Issue #987: Report missing GitHub token as a distinct CI `UNAVAILABLE` state

## Goal

When `mcp-coder check branch-status` runs **without a GitHub token**, today it mis-reports
CI as `NOT_CONFIGURED` ("CI not configured"), surfaces only a stderr `WARNING`, and the
`--ci-timeout` path can exit `2` before printing anything. This makes a *missing-auth*
problem look like a *no-CI* repo and gives the user nothing actionable.

This change introduces a distinct **`CIStatus.UNAVAILABLE`** state, detects the missing
token **proactively** via the upstream resolver `get_github_token()` (not by fragile
exception/string matching), surfaces an actionable hint **inside the printed report**
(human + LLM formats), degrades gracefully (still prints the partial rebase/task report),
and returns exit code `2`.

**Scope note:** Invalid-token (401/403) classification is explicitly *optional* in the
issue and is **excluded** here for simplicity. The `git fetch` hang risk is out of scope
(tracked upstream in mcp-workspace#219).

## Architectural / Design Changes

The design keeps a **single source of truth** for the state and reads it once for the
exit code:

1. **New CI state.** `CIStatus.UNAVAILABLE` ("unavailable — no token"), distinct from
   `NOT_CONFIGURED` (repo genuinely has no CI). Because `CIStatus` is a `str`-Enum and the
   ready-to-merge gate only lists `[PASSED, NOT_CONFIGURED]`, `UNAVAILABLE` is **excluded
   from ready-to-merge automatically** — no change needed to that gate.

2. **Proactive detection, not error-matching.** Detection reuses upstream's
   `get_github_token()` (`env → config → None`). A `None` result is the *only* signal for
   "token missing", so non-auth `ValueError`s upstream can never be misclassified.
   The symbol is re-exported through the `mcp_workspace_github` shim (CLAUDE.md forbids
   importing `mcp_workspace.*` directly); note it sources from `mcp_workspace.config`,
   not `github_operations`.

3. **Two detection sites, each minimal — by necessity, not duplication:**
   - **`_collect_ci_status`** sets the state. Required because `collect_branch_status()`
     is also called by internal callers/tests that bypass the CLI.
   - **`execute_check_branch_status`** only *gates the `--ci-timeout` wait* (one added
     boolean condition) so a missing token degrades to the partial report instead of
     raising exit `2` from the wait path.

4. **Message lives in the report, not in a second stderr emission.** The actionable hint
   is rendered inline on the `CI Status:` line (human) and appended to the summary line
   (LLM). This satisfies "visible regardless of log routing" with no duplicate plumbing
   and no new dataclass field.

5. **Exit code centralized.** The existing final return in `execute_check_branch_status`
   gains one line: `UNAVAILABLE → 2`. The partial report is `print()`ed *before* the
   return, so no information is lost. (Caller audit in the issue confirms exit `2` is safe.)

## Files Created / Modified

### Source (modified)
- `src/mcp_coder/mcp_workspace_github.py` — re-export `get_github_token` (from
  `mcp_workspace.config`) with a comment noting the cross-module source; add to `__all__`.
- `src/mcp_coder/checks/branch_status.py` — add `CIStatus.UNAVAILABLE`, a
  `GITHUB_TOKEN_HINT` constant, icon-map entry (🔒), inline rendering in
  `format_for_human`/`format_for_llm`, a recommendation branch, and the proactive
  detection early-return in `_collect_ci_status`.
- `src/mcp_coder/cli/commands/check_branch_status.py` — gate the `--ci-timeout` wait with
  `get_github_token()`, and add the `UNAVAILABLE → return 2` exit-code line.

### Tests (created / modified)
- `tests/checks/test_branch_status.py` — new `UNAVAILABLE` enum/value/icon, rendering, and
  recommendation tests; existing tests that mock `CIResultsManager` get `get_github_token`
  patched to return a token (so they keep their expected states).
- `tests/test_mcp_workspace_github_smoke.py` — assert `get_github_token` is importable
  from the shim.
- `tests/cli/commands/test_check_branch_status.py` — missing-token path skips the CI wait,
  prints the partial report with the hint, and returns exit `2`.

### Plan docs (created)
- `pr_info/steps/summary.md`, `pr_info/steps/step_1.md`, `pr_info/steps/step_2.md`,
  `pr_info/steps/step_3.md`.

## Implementation Steps (one commit each)

- **Step 1 — New state + presentation (data layer).** Enum value, constant, icon,
  human/LLM rendering, recommendation branch. Fully testable in isolation.
- **Step 2 — Detection (shim + `_collect_ci_status`).** Re-export `get_github_token`;
  early-return `UNAVAILABLE` when token missing; repair existing manager-mocking tests.
- **Step 3 — CLI integration.** Gate the `--ci-timeout` wait; centralized exit code `2`.

## Quality Gates (run after every step)
```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check  (extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```
Run `./tools/format_all.sh` before committing.
