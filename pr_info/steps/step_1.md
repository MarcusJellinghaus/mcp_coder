# Step 1 — Upstream integration + shared trust helper

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> Check the precondition first. Write the tests, then the code. Run pylint, mypy, and the fast pytest
> set (`-n auto`, integration markers excluded), plus vulture. Format, then make exactly one commit.

## Precondition

Check the project venv (`.venv`, not the Jenkins env, which the MCP search tools read) for the body-trust API
from mcp-workspace #369:

```
Select-String -Path ".venv\Lib\site-packages\mcp_workspace\github_operations\issues\body_trust.py" -Pattern "class BodyTrust\(|class BodyTrustResult\(|def check_body_trust\("
```

All three patterns must match.

- If any is missing: write one line to `pr_info/.blocked.txt`
  (`mcp-workspace #369 body-trust API not installed`) and stop.
- Real names (verified against mcp-workspace commit 359eea5): `IssueManager.check_body_trust(issue) -> BodyTrustResult`;
  enum `BodyTrust`; `BodyTrustResult`. Use these names in this step and in all later steps.

## WHERE

- `src/mcp_coder/mcp_workspace_github.py` — re-export `BodyTrust`, `BodyTrustResult`
- `tests/test_mcp_workspace_github_exports.py` — export test
- `vulture_whitelist.py` — entries for whatever vulture flags (e.g. enum members, result fields)
- `pyproject.toml` — minimum `mcp-workspace` version, **only if released**. First check whether the installed
  version, the one that has the body-trust API, is published on PyPI.
  - If it is released: set `"mcp-workspace>=<that version>"` in `dependencies`.
  - If it is not (for example, a git-HEAD build): leave `"mcp-workspace"` unpinned. The existing git override at
    `pyproject.toml:411` supplies the API until the release. The installed build is git HEAD
    (`0.1.14.dev41+g359eea5c7`); PyPI's latest is 0.1.13, so leave it unpinned.
- `src/mcp_coder/workflow_utils/issue_trust.py` — **new**
- `tests/workflow_utils/test_issue_trust.py` — **new**

## WHAT

```python
# workflow_utils/issue_trust.py
__all__ = ["evaluate_body_trust"]

def evaluate_body_trust(issue_manager: IssueManager, issue: IssueData) -> BodyTrustResult:
    """Return the body-trust result for issue; fail closed.

    Raises:
        GitHubRateLimitError: If the lookup hit a GitHub rate limit.
    """
```

## HOW

- Import `BodyTrustResult`, `BodyTrust`, `IssueData`, `IssueManager` from `mcp_coder.mcp_workspace_github`.
- Import `raise_if_rate_limited` from `mcp_coder.workflow_utils.rate_limit`.
- The helper does not log; callers log.

## ALGORITHM

```
try:
    return issue_manager.check_body_trust(issue)
except Exception as exc:  # broad on purpose: fail closed
    raise_if_rate_limited(exc)
    return BodyTrustResult(status=BodyTrust.LOOKUP_FAILED, reason=type(exc).__name__)
```

## DATA

The upstream `BodyTrustResult`, returned unchanged on success. On a non-rate-limit exception:
`BodyTrustResult(LOOKUP_FAILED, reason="<ExceptionTypeName>")`.

## Tests (`tests/workflow_utils/test_issue_trust.py`)

Use `MagicMock(spec=IssueManager)`.

- Trusted and untrusted results are passed through unchanged (`is` the same object).
- An upstream `LOOKUP_FAILED` result is passed through.
- `RuntimeError("secret text")` → `LOOKUP_FAILED`, reason `"RuntimeError"`, and `"secret text"` is not in the reason.
- `GitHubRateLimitError` → re-raised.
- A raw rate-limit exception that `to_rate_limit_error` recognises (build it the way `tests/workflow_utils/test_rate_limit.py` does) → `GitHubRateLimitError`.

Export test: parametrize `["BodyTrust", "BodyTrustResult"]`; assert each is an attribute of the shim and listed in `__all__`.
