# Step 8 — `vscodeclaude/workspace.setup_git_repo` (clone, corrupted-repo re-clone, pull)

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_8.md`. Implement step 8 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(vscodeclaude): workspace git setup via mcp_workspace_git`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `clone_repo` (from `mcp_workspace.git_operations.remotes`); `is_git_repository`, `pull` already exported
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` — `setup_git_repo` (~221–310); drop `execute_subprocess` / `CommandOptions` imports, keep `CalledProcessError`
- `tests/workflows/vscodeclaude/test_workspace_git.py`, `tests/workflows/vscodeclaude/test_workspace.py` (~148–166)

## WHAT

Contract unchanged: raises `CalledProcessError` on git failure (the caller `session_launch`
catches broadly, deletes the folder, re-raises); `ValueError` for a non-empty non-git folder.
`cmd` becomes the shim function name — no `"git"` list literal anywhere.

```python
if has_git and not is_git_repository(folder_path):
    # Corrupted git repo - delete and re-clone (same log + rmtree as today)
    ...
if is_empty:
    try:
        clone_repo(repo_url, folder_path)   # accepts an existing empty dir
    except ValueError as e:                 # message already credential-scrubbed
        raise CalledProcessError(1, "clone_repo", output=str(e)) from None
elif not has_git:
    raise ValueError(...)                   # unchanged
if not checkout_branch(branch, folder_path):
    raise CalledProcessError(1, "checkout_branch", output=f"Failed to checkout branch '{branch}'")
if not fetch_remote(folder_path):
    raise CalledProcessError(1, "fetch_remote", output="Failed to fetch from origin")
pulled = pull(folder_path)
if not pulled["success"]:
    raise CalledProcessError(1, "pull", output=pulled["error"], stderr=pulled["stderr"])
```

`from None` keeps the scrubbed message from regaining the URL via `__context__`.
Parity note: `is_git_repository` does not spawn git and is `True` for bare repos; a `.git`
that `Repo()` cannot open is still `False` → delete + re-clone.

## Tests (write first) — destructive-path parity

Patch `mcp_coder.workflows.vscodeclaude.workspace.{is_git_repository, clone_repo, checkout_branch, fetch_remote, pull}`.

- `.git` present, `is_git_repository` → `False`: folder contents deleted, `clone_repo(url, folder)` called, then checkout/fetch/pull.
- `.git` present, `is_git_repository` → `True`: no delete, no clone.
- empty folder → `clone_repo` called; `clone_repo` raises `ValueError("Failed to clone ...")` → `CalledProcessError` with `cmd == "clone_repo"`.
- `checkout_branch` `False` → `CalledProcessError(cmd="checkout_branch")`; `fetch_remote` `False` → `cmd="fetch_remote"`.
- `pull` `success=False` → `CalledProcessError(cmd="pull")`.
- non-empty folder without `.git` → `ValueError` (unchanged).
- Replace argv-substring fakes (`"rev-parse" in str(cmd)`, `"clone"`).

## DATA

- `None` / raises `CalledProcessError(returncode=1, cmd=<shim fn name>)` or `ValueError`.
