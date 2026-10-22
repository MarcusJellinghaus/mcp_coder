# Step 2 — Resolve via PR fallback, pre-create checks, exit code 3

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> TDD: first update and extend the tests in `tests/cli/commands/test_gh_tool_checkout.py`,
> then change `execute_checkout_issue_branch()` in `src/mcp_coder/cli/commands/gh_tool.py`
> and add `_find_precreate_candidates()`. Keep it minimal (KISS). Run pylint,
> pytest (fast unit set, `-n auto`), mypy, ruff and lint-imports; all must pass.
> Run `run_format_code`, then make exactly one commit.

## Preconditions

- If the installed `IssueBranchManager` (check with `get_library_source`) lacks
  `get_branch_with_pr_fallback` or `get_linked_branch_and_closing_prs_or_none`, write one
  line to `pr_info/.blocked.txt` and stop.
- If lint-imports reports a broken contract for `mcp_coder.cli.commands.gh_tool ->
  mcp_coder.utils.subprocess_runner`, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/cli/commands/gh_tool.py`
- `tests/cli/commands/test_gh_tool_checkout.py`

## WHAT

```python
def _find_precreate_candidates(
    branch_manager: IssueBranchManager, project_dir: Path, issue_number: int
) -> dict[str, str] | None:
    """Collect existing branches for the issue before creating one.

    Returns:
        Ordered mapping of branch name -> source label (first source wins),
        or None if the linkage lookup or ``git ls-remote`` failed.
    """
```

`execute_checkout_issue_branch(args) -> int` keeps its signature. Its docstring documents
the resolution order (fallback, then pre-create checks, then create) and exit codes 0–3,
as in the summary table.

## HOW

New imports in `gh_tool.py`:

```python
import re
from pathlib import Path
from mcp_coder.mcp_workspace_git import checkout_branch, fetch_remote, get_repository_identifier
from ...utils.subprocess_runner import execute_command
```

Tests patch everything at `mcp_coder.cli.commands.gh_tool.<name>`: `IssueManager`,
`IssueBranchManager`, `get_repository_identifier`, `execute_command`, `fetch_remote`,
`checkout_branch`, `resolve_project_dir`.

## ALGORITHM

`execute_checkout_issue_branch`, after the existing issue-not-found check:

```
repo_id = get_repository_identifier(project_dir); if None: log error, return 2
mgr = IssueBranchManager(project_dir=project_dir, repo_url=repo_id.https_url)
branch = mgr.get_branch_with_pr_fallback(issue_number, repo_id.owner, repo_id.repo_name)
if branch is None:
    cands = _find_precreate_candidates(mgr, project_dir, issue_number); None -> log error, return 2
    1 cand -> log INFO label, branch = it;  >=2 -> log error listing labels, return 3
    0 -> create_remote_branch_for_issue(...) as today (failure -> return 1)
checkout + print as today
```

`_find_precreate_candidates`:

```
result = mgr.get_linked_branch_and_closing_prs_or_none(n); None -> log error, return None
ls = execute_command(["git", "ls-remote", "--heads", "origin"], cwd=str(project_dir))
if ls.return_code != 0: log error (ls.stderr), return None
pattern = re.compile(rf"(^|/){n}[-_]")
cands = {}; for b in linked: cands.setdefault(b, f"linked branch {b}")
for pr in closing: setdefault(pr.head_ref_name, f"closing PR #{pr.number} -> {pr.head_ref_name}")
for line in ls.stdout.splitlines(): name = last tab field minus "refs/heads/"; if pattern.search(name): setdefault(name, f"remote branch {name}")
return cands
```

## DATA

- `ls-remote` line format: `<sha>\trefs/heads/<branch>`
- `closing_prs` items: `ClosingPRRef` with `.number` and `.head_ref_name`
- Test mocks:
  - `repo_id` is a `MagicMock` with `owner`, `repo_name`, `https_url`.
  - `execute_command` returns `MagicMock(return_code=0, stdout="...", stderr="")`.
  - The closing-PR mock is `MagicMock(number=42, head_ref_name="123-b")`.

## Tests (in `test_gh_tool_checkout.py`)

Replace every `get_linked_branches` mock with a `get_branch_with_pr_fallback` mock. Add
fixtures `mock_repo_identifier` (default: a valid repo id) and `mock_execute_command`
(default: `return_code=0`, empty stdout). On the create path, set
`get_linked_branch_and_closing_prs_or_none.return_value = ([], [])`.

- Existing tests, adapted: fallback hit → exit 0; create → exit 0; creation fails → 1;
  checkout fails → 2; issue not found → 1; invalid dir → 2; unexpected error → 2;
  `base_branch` passthrough; fetch called.
- New: with a PR open and `linkedBranches` empty, the fallback returns the PR head → exit 0,
  `create_remote_branch_for_issue` not called, and `get_linked_branch_and_closing_prs_or_none`
  not called.
- New, parametrized single-candidate (exit 0, that branch checked out, no create, label in
  INFO log): one linked; one closing PR; one remote match; the closing-PR head is also the
  remote branch (dedupe → one candidate); remote `feature/123_x` matches while `1234-x` is
  ignored.
- New, parametrized ambiguous (exit 3, all labels in the log, no create): two linked
  branches (replaces `test_checkout_uses_first_linked_branch`); linked + closing PR with a
  different head; two remote matches.
- New, parametrized exit 2 (no create): `get_repository_identifier` returns `None`; lookup
  returns `None`; `ls-remote` `return_code=1`; the fallback raises `ValueError`.
- Update the `TestCheckoutIssueBranchExitCodes` docstring to "(0, 1, 2, 3)".
