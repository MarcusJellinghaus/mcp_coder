# Summary: Prep — `BaseGitHubManager` token param + `transition_issue_label` primitive

Issue: #832 — Part 1 of 5-issue cross-repo refactor.

## Goal

Internal prep refactors in `mcp_coder` so the upcoming cross-repo move of `git_operations` / `github_operations` to `mcp_workspace` (issues ② and ④) is mechanical. No public API break, no new dependencies, one intentional narrow behavior improvement.

## Architectural / design changes

### 1. Token injection (backward-compatible)

`BaseGitHubManager` currently reads the GitHub token itself via `user_config.get_config_values(...)`. After this prep, subclasses accept an explicit `github_token` kwarg that propagates to the base class. The base class uses the explicit value when provided, and falls back to `user_config` lookup when `None`.

- Enables future consumers (shim in issue ⑤) to inject a pre-resolved token without depending on `user_config`.
- Existing callers pass nothing → fallback behavior unchanged.
- Token param added to **all 5 subclasses** (`IssueManager`, `IssueBranchManager`, `PullRequestManager`, `LabelsManager`, `CIResultsManager`) — the only way it's reachable.
- **Asymmetry preserved**: `LabelsManager` / `PullRequestManager` still accept only `project_dir` — only `github_token` is added; `repo_url` is NOT introduced to them.

### 2. `transition_issue_label` primitive — separation of concerns

`IssueManager.update_workflow_label` today does three things: branch/issue resolution, `labels.json` lookup, and the label-set mutation on GitHub. Introducing a clean primitive splits the last concern into a reusable, config-free operation:

- New public method `transition_issue_label(issue_number, new_label, labels_to_clear)` lives on `LabelsMixin` alongside `add_labels`/`remove_labels`/`set_labels`.
- Knows nothing about `labels.json`, `internal_id`, or branches. Pure label math.
- Fetches current labels itself via `self.get_issue(...)` — callers don't pass them in.
- Idempotent: if target label already present AND no overlap with `labels_to_clear`, skips the `set_labels` API call.
- Decorated with `@_handle_github_errors(default_return=False)` — matches `add_labels`/`remove_labels`/`set_labels`. `ValueError` and 401/403 propagate.

`update_workflow_label` retains its public signature and all branch/label-config resolution, but delegates the actual label mutation + idempotency + current-labels fetch to the primitive. Former step 6 (duplicate `get_issue` + `number==0` check) and step 7 (legacy idempotency block) are removed — both are now owned by the primitive.

### 3. Intentional narrow behavior improvement (accepted)

Today's step-7 idempotency check returns `True` without touching labels when the target label is present AND source label is absent — even if other stray workflow labels linger. The primitive's stricter idempotency check (target present AND no overlap with `labels_to_clear`) cleans up such strays instead. Example: issue has `code_review` + stale `planning` + no `implementing` → today returns True silently; post-refactor strips `planning`. Consistent with `test_update_workflow_label_removes_different_workflow_label`.

## Out of scope

- No moves to `mcp_workspace` (issues ②/④).
- No shim creation (issues ③/⑤).
- No `user_config` removal from `BaseGitHubManager` (issue ⑤).
- No harmonizing `LabelsManager` / `PullRequestManager` with `repo_url`.
- No `labels.json` / `label_config.py` edits.
- No dependency bump.
- No change to `update_workflow_label`'s public signature.

## Files — created / modified

### Modified (source)
- `src/mcp_coder/utils/github_operations/base_manager.py` — add `github_token` param to `BaseGitHubManager.__init__`, skip `user_config` when provided.
- `src/mcp_coder/utils/github_operations/issues/manager.py` — forward `github_token` in `IssueManager.__init__`; refactor `update_workflow_label` to delegate to `transition_issue_label`.
- `src/mcp_coder/utils/github_operations/issues/branch_manager.py` — forward `github_token` in `IssueBranchManager.__init__`.
- `src/mcp_coder/utils/github_operations/pr_manager.py` — forward `github_token` in `PullRequestManager.__init__`.
- `src/mcp_coder/utils/github_operations/labels_manager.py` — forward `github_token` in `LabelsManager.__init__`.
- `src/mcp_coder/utils/github_operations/ci_results_manager.py` — forward `github_token` in `CIResultsManager.__init__`.
- `src/mcp_coder/utils/github_operations/issues/labels_mixin.py` — add `transition_issue_label` method.

### Modified (tests)
- `tests/utils/github_operations/test_base_manager.py` — add parametrized token-forwarding test over all 5 subclasses.
- `tests/utils/github_operations/test_issue_manager_labels.py` — add `TestTransitionIssueLabel` class.

### No new files, no new folders

## Steps overview

- **Step 1**: `github_token` parameter — `BaseGitHubManager` + all 5 subclass forwards + parametrized forwarding test.
- **Step 2**: `transition_issue_label` primitive on `LabelsMixin` + `TestTransitionIssueLabel` tests.
- **Step 3**: Refactor `update_workflow_label` to use the primitive; remove redundant step 6 / step 7. Existing tests act as regression coverage.

Each step is a single self-contained commit with tests + implementation + all quality checks passing (pylint, pytest, mypy, ruff, lint-imports).
