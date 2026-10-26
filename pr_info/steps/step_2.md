# Step 2 — `workflow_steps/rebase._base_sha`

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement step 2 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(rebase-step): read base sha via mcp_workspace_git`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `get_remote_branch_commit_sha` (from `mcp_workspace.git_operations.branch_queries`)
- `src/mcp_coder/workflow_steps/rebase.py` — `_base_sha`
- `tests/workflow_steps/test_rebase.py` — the `_base_sha` tests and any `execute_command` patch that serves the `rev-parse` call

## WHAT

```python
def _base_sha(project_dir: Path, base: str) -> str | None:
    sha = get_remote_branch_commit_sha(project_dir, base)
    return sha[:SHORT_SHA_LENGTH] if sha else None
```

Upstream never raises and takes the branch name **without** `origin/`. The broad `try` goes.
`execute_command` stays imported in this module until step 11 (merge-tree probe).

## Tests (write first)

- patched `get_remote_branch_commit_sha` returns a 40-char sha → `_base_sha` returns the first `SHORT_SHA_LENGTH` chars; called with `(project_dir, "main")`.
- returns `None` → `_base_sha` returns `None`.
- Update `_attempt_rebase_and_push` tests that fed the `rev-parse` call through an `execute_command` side-effect: patch `get_remote_branch_commit_sha` instead (keep the merge-tree `execute_command` patches for now).

## DATA

- `str | None` short sha, unchanged contract.
