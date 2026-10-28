# Step 4 — Manager construction fixes (never both `project_dir` and `repo_url`)

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`).
> Implement only Step 4. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/services/branch_info.py` (`get_pr_for_issue`, ~line 168)
- `src/mcp_coder/cli/commands/gh_tool.py` (`execute_checkout_issue_branch`, ~line 154)
- `src/mcp_coder/workflow_utils/label_transitions.py` (Step 3 block, ~lines 94-106)
- `src/mcp_coder/workflows/vscodeclaude/checks.py` (`_build_pr_manager`, import line 11)
- tests: `tests/services/test_branch_info.py`, `tests/cli/commands/test_gh_tool_checkout.py`,
  `tests/workflow_utils/test_label_transitions.py`, `tests/workflows/vscodeclaude/test_checks.py`

## WHAT
- `branch_info.py`: `IssueBranchManager(project_dir=project_dir)`.
- `gh_tool.py`: `IssueBranchManager(project_dir=project_dir)`.
- `label_transitions.py`:
  ```python
  if issue_manager.project_dir is not None:
      branch_manager = IssueBranchManager(
          project_dir=issue_manager.project_dir, github_token=issue_manager.github_token
      )
  else:
      branch_manager = IssueBranchManager(
          repo_url=issue_manager.repo_identifier.https_url,
          github_token=issue_manager.github_token,
      )
  ```
  Remove the `__new__` + `BaseGitHubManager.__init__` workaround, the
  `_cached_repo_identifier` use and the `BaseGitHubManager` import.
- `checks.py`: delete `_build_pr_manager` and the `BaseGitHubManager` import;
  use `PullRequestManager(repo_url=repo_url)` in `check_pr_health`.

## HOW
Unmocked constructor tests (TDD) — the real `IssueBranchManager` class is used
so a both-arguments call raises `ValueError("Exactly one of project_dir or repo_url ...")`:
- Use a temporary git repo with a GitHub `origin` remote (`tmp_path`, existing
  git test helpers/fixtures if present) and `monkeypatch.setenv("GITHUB_TOKEN", "x")`.
  Patch only the network method (`IssueBranchManager.get_branch_with_pr_fallback` /
  `is_branch_linked_to_issue`) — **not** the constructor.
- `branch_info.get_pr_for_issue(repo, 1)` does not raise `ValueError`.
- `gh-tool checkout-issue-branch`: the constructor is reached without `ValueError`
  (patch `IssueManager.get_issue`, `get_branch_with_pr_fallback`, `checkout_branch`).
- `update_workflow_label` with a project-dir `IssueManager`, branch name given,
  and `_cached_repo_identifier` already resolved: `is_branch_linked_to_issue`
  is called (proves construction succeeded).
- Remove the existing mocks that hid the bug where they patch the
  `IssueBranchManager` class in those three test modules, or keep them only in
  tests unrelated to construction.
- `checks.py`: existing PR-health tests patch `_build_pr_manager`; switch them to
  patch `PullRequestManager` in the `checks` module.

## DATA
No return types change.
