# Step 1 — Add `github_token` parameter to `BaseGitHubManager` and forward through all 5 subclasses

## LLM prompt

> Read `pr_info/steps/summary.md` for context, then implement **this step only** (`pr_info/steps/step_1.md`) in a single commit. Use TDD: write the test first, then the implementation, then run all quality checks (`mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check` with `-n auto` and the unit-test marker-exclusion filter, `mcp__tools-py__run_mypy_check`, ruff, lint-imports). Do not start Step 2. Do not touch `transition_issue_label` or `update_workflow_label` in this step.

## WHERE

- `src/mcp_coder/utils/github_operations/base_manager.py` — modify `BaseGitHubManager.__init__`
- `src/mcp_coder/utils/github_operations/issues/manager.py` — modify `IssueManager.__init__`
- `src/mcp_coder/utils/github_operations/issues/branch_manager.py` — modify `IssueBranchManager.__init__`
- `src/mcp_coder/utils/github_operations/pr_manager.py` — modify `PullRequestManager.__init__`
- `src/mcp_coder/utils/github_operations/labels_manager.py` — modify `LabelsManager.__init__`
- `src/mcp_coder/utils/github_operations/ci_results_manager.py` — modify `CIResultsManager.__init__`
- `tests/utils/github_operations/test_base_manager.py` — add parametrized token-forwarding test

## WHAT — function signatures

### Base class
```python
class BaseGitHubManager:
    def __init__(
        self,
        project_dir: Optional[Path] = None,
        repo_url: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> None: ...
```

### Subclasses
```python
class IssueManager(...):
    def __init__(
        self,
        project_dir: Optional[Path] = None,
        repo_url: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> None: ...

class IssueBranchManager(BaseGitHubManager):
    def __init__(
        self,
        project_dir: Optional[Path] = None,
        repo_url: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> None: ...

class PullRequestManager(BaseGitHubManager):
    def __init__(
        self,
        project_dir: Optional[Path] = None,
        github_token: Optional[str] = None,
    ) -> None: ...

class LabelsManager(BaseGitHubManager):
    def __init__(
        self,
        project_dir: Optional[Path] = None,
        github_token: Optional[str] = None,
    ) -> None: ...

class CIResultsManager(BaseGitHubManager):
    def __init__(
        self,
        project_dir: Optional[Path] = None,
        repo_url: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> None: ...
```

## HOW — integration

- Plain typed keyword param, default `None`. **No `*` keyword-only marker** (matches style of `project_dir` / `repo_url`).
- Each subclass forwards via `super().__init__(..., github_token=github_token)`.
- `PullRequestManager` / `LabelsManager` forward only `project_dir` + `github_token` (no `repo_url` — signature asymmetry preserved per issue decision #9).
- Update docstrings to mention the new param. Keep existing error messages unchanged.

## ALGORITHM — token resolution in `BaseGitHubManager.__init__`

Keep existing directory/URL validation order (validate dir/URL FIRST, then token — preserves specific error precedence). Replace the current `user_config` call block with:

```
if github_token is not None:
    raw_token = github_token
else:
    config = user_config.get_config_values([("github", "token", None)])
    raw_token = config[("github", "token")]
if not isinstance(raw_token, str):
    raise ValueError("GitHub token not found. ...")   # existing message
self.github_token = raw_token
self._github_client = Github(auth=Auth.Token(raw_token))
```

## DATA

- No new data structures. `self.github_token: str` attribute already exists.
- Behavior change: when `github_token` is explicit and a non-empty string, `user_config.get_config_values` is NOT called.

## Test (write first)

In `tests/utils/github_operations/test_base_manager.py`, add a new class `TestGithubTokenForwarding` with a parametrized test covering all 5 subclasses:

```python
@pytest.mark.parametrize(
    "manager_cls, init_kwargs",
    [
        (IssueManager,        {"project_dir": <mock_path>}),
        (IssueBranchManager,  {"project_dir": <mock_path>}),
        (PullRequestManager,  {"project_dir": <mock_path>}),
        (LabelsManager,       {"project_dir": <mock_path>}),
        (CIResultsManager,    {"project_dir": <mock_path>}),
    ],
)
def test_explicit_github_token_bypasses_user_config(manager_cls, init_kwargs) -> None:
    # Patch is_git_repository → True, get_github_repository_url where needed,
    # user_config.get_config_values (assert NOT called), and Github class.
    # Instantiate with github_token="explicit-token".
    # Assert manager.github_token == "explicit-token".
    # Assert user_config.get_config_values was not called.
```

Also add a second test verifying the fallback still works (token=None → `user_config.get_config_values` IS called, token comes from config).

## Acceptance (local checks)

- `pytest -n auto -m "not <integration markers>"` → all pass.
- pylint / mypy / ruff / lint-imports → clean.
- No existing test required to change.

## Scope guard

- Do NOT add `transition_issue_label`.
- Do NOT modify `update_workflow_label`.
- Do NOT touch `labels.json`, `label_config.py`, or any caller of the managers.
- Do NOT add `repo_url` to `LabelsManager` or `PullRequestManager`.
