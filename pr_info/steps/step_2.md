# Step 2: Add `_push_after_commit` helper with unit tests

**Ref:** See `pr_info/steps/summary.md` for full context (issue #907).

## WHERE

- `src/mcp_coder/cli/commands/commit.py` — new helper function + new imports
- `tests/cli/commands/test_commit.py` — new test class

## WHAT

```python
def _push_after_commit(project_dir: Path) -> int:
```

Uses the existing module-level `logger`.

## HOW

Add new imports to `commit.py`:

```python
from mcp_coder.mcp_workspace_git import (
    # ... existing imports ...,
    get_current_branch_name,
    get_default_branch_name,
    git_push,
    has_remote_tracking_branch,
    push_branch,
)
```

## ALGORITHM

```
branch = get_current_branch_name(project_dir)
default = get_default_branch_name(project_dir)  # may return None
blocked = {default} if default else {"main", "master"}
if branch in blocked → log error, return 2
if not has_remote_tracking_branch(branch, project_dir):
    success = push_branch(branch, project_dir, set_upstream=True)  # returns bool
else:
    result = git_push(project_dir)  # returns dict
    success = result["success"]
if success → log "Pushed to origin/<branch>", return 0
else → log "Failed to push to origin: <error>", return 2
```

## DATA

- **Input:** `project_dir: Path`
- **Returns:** `int` — exit code (0 success, 2 failure)
- `push_branch()` returns `bool`
- `git_push()` returns `dict` with `"success"` key

## Tests (write first)

Add `TestPushAfterCommit` class in `tests/cli/commands/test_commit.py`. All tests patch the five imported git functions on the `mcp_coder.cli.commands.commit` module.

1. **`test_push_success_with_tracking_branch`** — `has_remote_tracking_branch` returns `True`, `git_push` returns `{"success": True}`. Assert returns 0, log contains `"Pushed to origin/"`.
2. **`test_push_success_new_branch`** — `has_remote_tracking_branch` returns `False`, `push_branch` returns `True`. Assert returns 0, assert `push_branch` called with `set_upstream=True`.
3. **`test_push_refused_on_default_branch`** — `get_default_branch_name` returns `"main"`, `get_current_branch_name` returns `"main"`. Assert returns 2, log contains error.
4. **`test_push_refused_fallback_main`** — `get_default_branch_name` returns `None`, `get_current_branch_name` returns `"main"`. Assert returns 2.
5. **`test_push_refused_fallback_master`** — `get_default_branch_name` returns `None`, `get_current_branch_name` returns `"master"`. Assert returns 2.
6. **`test_push_failure_with_tracking`** — `git_push` returns `{"success": False, "error": "rejected"}`. Assert returns 2, log contains `"Failed to push"`.
7. **`test_push_failure_new_branch`** — `push_branch` returns `False`. Assert returns 2, log contains `"Failed to push"`.

## Commit

`feat(cli): add _push_after_commit helper with safety guards`

---

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context, then implement step 2.
> Add the `_push_after_commit(project_dir: Path) -> int` helper to `src/mcp_coder/cli/commands/commit.py` with the new imports from `mcp_workspace_git`.
> Write tests first in `tests/cli/commands/test_commit.py`. Patch all git functions on the `mcp_coder.cli.commands.commit` module path.
> Run all code quality checks. Commit with message: `feat(cli): add _push_after_commit helper with safety guards`
