# Step 2 — Detection: shim re-export + `_collect_ci_status` early-return

> Read `pr_info/steps/summary.md` first. Depends on Step 1 (the `UNAVAILABLE` state must
> already exist). This step makes `collect_branch_status()` actually *produce*
> `UNAVAILABLE` when no GitHub token is configured.

## WHERE
- Source: `src/mcp_coder/mcp_workspace_github.py` (shim re-export)
- Source: `src/mcp_coder/checks/branch_status.py` (`_collect_ci_status`)
- Tests:  `tests/test_mcp_workspace_github_smoke.py`, `tests/checks/test_branch_status.py`

## WHAT

### 2a. Shim re-export (`mcp_workspace_github.py`)
`get_github_token` lives in `mcp_workspace.config`, **not** `github_operations`. Add a
dedicated import with a clarifying comment, and add it to `__all__`:
```python
# Sourced from mcp_workspace.config (not github_operations): GitHub token resolver
# (env var → config file → None). Re-exported here so callers obey the CLAUDE.md rule
# against importing mcp_workspace.* directly.
from mcp_workspace.config import get_github_token
```
Add `"get_github_token"` to the `__all__` list.

### 2b. Detection in `_collect_ci_status` (`branch_status.py`)
- Extend the existing import to include `get_github_token`:
  ```python
  from mcp_coder.mcp_workspace_github import (
      CIResultsManager,
      IssueData,
      IssueManager,
      get_github_token,
  )
  ```
- Add a proactive guard as the **first thing inside the `try`**, before
  `ci_manager = CIResultsManager(project_dir)`:
  ```python
  if get_github_token() is None:
      logger.info("GitHub token not configured — CI status unavailable")
      return CIStatus.UNAVAILABLE, None
  ```

`get_github_token()` is zero-arg (`env → config → None`). Do **not** add a helper or
thread `project_dir` through it.

## HOW (integration points)
- Signature unchanged: `_collect_ci_status(project_dir, branch, max_lines) -> Tuple[CIStatus, Optional[str]]`.
- The new early-return precedes all network/manager construction, so a missing token
  never reaches `CIResultsManager`.

## ALGORITHM (pseudocode)
```
def _collect_ci_status(...):
    try:
        if get_github_token() is None:
            return UNAVAILABLE, None
        ci_manager = CIResultsManager(project_dir)
        ... existing logic unchanged ...
    except Exception:
        return NOT_CONFIGURED, None    # unchanged fallback
```

## DATA
- Token missing → `(CIStatus.UNAVAILABLE, None)`.
- Token present → unchanged existing behavior (PASSED / FAILED / PENDING / NOT_CONFIGURED).
- `from mcp_coder.mcp_workspace_github import get_github_token` resolves.

## TESTS (write first — TDD)
1. **Shim smoke** (`tests/test_mcp_workspace_github_smoke.py`): assert
   `get_github_token` is importable from `mcp_coder.mcp_workspace_github` and is callable.
   **Also bump the `__all__` count assertion** in `test_all_exports_defined`: adding
   `"get_github_token"` grows `__all__` from 24 → 25, so change
   `assert len(__all__) == 24` to `assert len(__all__) == 25`. (Verified: the shim's
   `__all__` currently lists exactly 24 symbols.) This must land in Step 2 so its pytest
   gate stays green.
2. **Detection** (`tests/checks/test_branch_status.py`): patch
   `mcp_coder.checks.branch_status.get_github_token` to return `None` →
   `_collect_ci_status(...)` returns `(CIStatus.UNAVAILABLE, None)` **without**
   constructing a `CIResultsManager`. Patch it to return `"tok"` and assert existing
   PASSED/FAILED/NOT_CONFIGURED paths still work (with `CIResultsManager` mocked).
3. **Existing-test repair (important):** the tests that call `_collect_ci_status`
   **directly** and mock only `CIResultsManager` will now hit the token early-return and
   return `UNAVAILABLE` on a token-less runner. For each, patch
   `mcp_coder.checks.branch_status.get_github_token` to return a dummy token (e.g. `"tok"`)
   so they keep their expected states. Confirmed affected tests in
   `tests/checks/test_branch_status.py` (verified against the current file):
   - `test_collect_ci_status_with_truncation` (~line 900; asserts `FAILED`).
   - `test_collect_ci_status_no_truncation` (~line 935; asserts `PASSED`).
   - `test_collect_ci_status_error_handling` (~line 953, assert at ~line 964; asserts
     `NOT_CONFIGURED`).

   **Not affected — do not touch:** `test_create_empty_report` (~line 286) does *not* call
   `_collect_ci_status` (it calls `create_empty_report`), so the earlier citation of
   line ~292 was a false positive and is dropped. Tests that patch `_collect_ci_status`
   itself (e.g. the `collect_branch_status` tests) are also unaffected — they never reach
   the early-return.

## COMMIT
Single commit: shim re-export + detection + tests + existing-test repair, all checks green.

## QUALITY GATES
```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check (extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```
Run `./tools/format_all.sh` before committing.

## LLM PROMPT
> Implement Step 2 from `pr_info/steps/step_2.md` (context in `pr_info/steps/summary.md`).
> (a) In `src/mcp_coder/mcp_workspace_github.py`, re-export `get_github_token` from
> `mcp_workspace.config` (with the cross-module comment) and add it to `__all__`.
> (b) In `src/mcp_coder/checks/branch_status.py`, import `get_github_token` and add an
> early `return CIStatus.UNAVAILABLE, None` at the top of the `try` in `_collect_ci_status`
> when `get_github_token() is None`. Follow TDD: add the smoke + detection tests first, and
> bump `test_all_exports_defined`'s `assert len(__all__) == 24` to `== 25`. Then patch
> `mcp_coder.checks.branch_status.get_github_token` to return a dummy token in the three
> tests that call `_collect_ci_status` directly (`test_collect_ci_status_with_truncation`,
> `test_collect_ci_status_no_truncation`, `test_collect_ci_status_error_handling`) so they
> keep their expected states. Use only MCP tools per CLAUDE.md, run pylint/pytest/mypy, and
> produce exactly one commit.
