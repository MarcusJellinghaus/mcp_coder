# Step 7 — `vscodeclaude/session_restart` fetch / checkout / pull

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`. Implement step 7 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(vscodeclaude): restart branch prep via mcp_workspace_git`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `pull` (from `mcp_workspace.git_operations.remotes`)
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py` — `_prepare_restart_branch` (~59–119); drop `execute_subprocess` / `CommandOptions` imports, keep `CalledProcessError`
- `tests/workflows/vscodeclaude/test_session_restart_prepare_branch.py`, `test_session_restart_branch_integration.py` (~317, ~390), `test_session_restart_closed_sessions.py` (~412, ~575–594)

## WHAT

Migrate the whole function together; outcomes unchanged (`"Git error"` on any git failure).

```python
# 1. fetch (fatal if fails)
if not fetch_remote(folder_path):
    logger.error("git fetch failed for %s", folder_path)
    return BranchPrepResult(False, "Git error", None)
# 2-4 unchanged (status gate, linked branch, dirty check)
# 5. checkout + pull
try:
    if not checkout_branch(linked_branch, folder_path):
        raise CalledProcessError(1, "checkout_branch", output=f"Failed to checkout '{linked_branch}'")
    pulled = pull(folder_path)
    if not pulled["success"]:
        raise CalledProcessError(1, "pull", output=pulled["error"], stderr=pulled["stderr"])
except CalledProcessError as e:
    logger.error("Git operation failed: %s", e)
    return BranchPrepResult(False, "Git error", None)
```

`fetch_remote` / `checkout_branch` return `bool`; `pull` returns `GitResult` (never raises).
Imports: `from ...mcp_workspace_git import checkout_branch, fetch_remote, pull`.

## Tests (write first)

Patch `mcp_coder.workflows.vscodeclaude.session_restart.{fetch_remote, checkout_branch, pull}`.

- fetch `False` → `(False, "Git error", None)`; checkout/pull not called.
- status not requiring a branch → `(True, None, None)` after fetch.
- checkout `False` → `"Git error"`, pull not called.
- pull `success=False` → `"Git error"`.
- happy path → `(True, None, linked_branch)`; `checkout_branch(linked_branch, folder_path)` and `pull(folder_path)` called.
- Replace every `execute_subprocess` side-effect keyed on argv (`"fetch" in cmd`, `"checkout"`, `"pull"`, `"rev-parse"`) in the three test files.

## DATA

- `BranchPrepResult` unchanged.
