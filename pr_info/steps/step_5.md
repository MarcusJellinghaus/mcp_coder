# Step 5 — `gh_tool` remote branch candidates

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement step 5 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(gh-tool): list origin branches via mcp_workspace_git`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `list_remote_branches` (from `mcp_workspace.git_operations.remotes`)
- `src/mcp_coder/cli/commands/gh_tool.py` — `_find_precreate_candidates` (~line 91); drop the `execute_command` import
- `tests/cli/commands/test_gh_tool_checkout.py` — fixture `mock_execute_command` (~59) and its users

## WHAT

Replace the `execute_command(["git", "ls-remote", "--heads", "origin"])` block and the
stdout parsing loop:

```python
remote = list_remote_branches(project_dir)
if not remote["success"]:
    logger.error("git ls-remote failed: %s", remote["stderr"] or remote["error"])
    return None
...
for name in remote["branches"]:  # already stripped of refs/heads/
    if pattern.search(name):
        candidates.setdefault(name, f"remote branch {name}")
```

Failure is `success=False`, never `[]` → still `None` (exit 2 path). **Not** `remote_branch_exists`.
Docstring "or `git ls-remote` failed" can stay (upstream runs ls-remote).

## Tests (write first)

- Rename fixture to `mock_list_remote_branches` patching `mcp_coder.cli.commands.gh_tool.list_remote_branches`,
  default return `{"success": True, "error": None, "returncode": 0, "stderr": "", "branches": []}`.
- `branches=["123-feature", "other"]` → one candidate `"remote branch 123-feature"`.
- `success=False` → `_find_precreate_candidates` returns `None`, command exits 2.
- Update tests that fed ls-remote stdout lines (`"<sha>\trefs/heads/x"`) to pass branch names.

## DATA

- `RemoteBranchesResult` keys read: `success`, `branches`, `stderr`, `error`.
