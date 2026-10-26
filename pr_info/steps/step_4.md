# Step 4 — `check_base_branch_on_origin`

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement step 4 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(base-branch): probe origin via mcp_workspace_git`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `probe_origin_branch` (from `mcp_workspace.git_operations.remotes`)
- `src/mcp_coder/workflow_utils/base_branch.py` — `check_base_branch_on_origin`; drop the `execute_command` import
- `tests/workflow_utils/test_base_branch.py` (~449–475)

## WHAT

```python
def check_base_branch_on_origin(project_dir: Path, base_branch: str) -> str | None:
    probe = probe_origin_branch(project_dir, base_branch)
    if probe["exists"] is True:
        return None
    detail = (probe["stderr"] or probe["error"] or "").strip()
    message = f"Base branch '{base_branch}' not found on origin; create and push it first"
    return f"{message} ({detail})" if detail else message
```

**Not** `remote_branch_exists` (local refs, stale). `exists=None` (origin unreachable / auth)
is still an error message — same message, the detail names the cause. Docstring: replace
"`git ls-remote`" wording with "asks origin directly (`probe_origin_branch`)".

## ALGORITHM

```
probe = probe_origin_branch(dir, base)
if probe.exists is True -> None
detail = stderr or error (stripped)
return message + " (detail)" if detail else message
```

## Tests (write first) — parity of the error message

- `exists=True` → `None`; called with `(project_dir, "main")`.
- `exists=False`, `stderr=""`, `error=None` → exactly `"Base branch 'main' not found on origin; create and push it first"`.
- `exists=None`, `stderr="fatal: could not read from remote"` → message ends with `"(fatal: could not read from remote)"` (stderr detail kept).
- `exists=None`, `stderr=None`, `error="Not a git repository: ..."` → detail is the error.

## DATA

- `BranchProbe` keys read: `exists`, `stderr`, `error`. Return `str | None` unchanged.
