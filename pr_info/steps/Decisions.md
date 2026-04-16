# Plan Review Decisions Log

## Round 1 (2026-04-16)

1. **Accept loss of the INFO log `'Source label ... not present'`** in `update_workflow_label` after delegation to `transition_issue_label`. The primitive is config-free and cannot distinguish source vs clear-set labels. No tests assert this log. Captured in `step_3.md` ("Delete from the old body") and in `summary.md` ("Intentional narrow behavior improvement").

2. **Primitive owns the empty-`IssueData` guard from `get_issue`.** Explicitly check `issue["number"] == 0` after `get_issue` and return `False`; do not rely on the `@_handle_github_errors` decorator alone (it doesn't cover `get_issue`'s own `default_return` sentinel). Without this guard, `set_labels(issue_number=0, ...)` would raise `ValueError` via `validate_issue_number`. New test case `test_transition_get_issue_failure_returns_false` added.

3. **`TestTransitionIssueLabel` is decorated with `@pytest.mark.git_integration`** for file-level consistency with the sibling `TestIssueManagerLabels` class in the same file (the sibling already uses the marker even for mocked tests). The sibling class itself is not changed.

4. **Name the mocking style for the Step 1 token-forwarding test:** `Mock(spec=Path)` + patch `mcp_coder.utils.github_operations.base_manager.is_git_repository` returning `True`, matching `TestBaseGitHubManagerWithProjectDir` in `test_base_manager.py`. Primary assertion: patch `user_config.get_config_values` and assert NOT called when `github_token` is explicit; IS called when `github_token=None`.

5. **Bound the docstring update scope** in Step 1: add a single-line `github_token: Optional explicit token ...` entry under the Args section of each modified `__init__` docstring. Do not reformat or rewrite other docstring content.

6. **Log-string assertion caveat for Step 3 regression tests:** before running, skim listed test assertions and confirm none rely on the dropped `'Source label ... not present'` or step-7 `'already has ... without ...'` log strings. If any do, update the assertion to check behaviour (e.g. `set_labels` call count or absence) rather than log text.
