# Step 2 — Exit-code regression test for unverifiable branch protection

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`. This step
> only adds a test: the behaviour is already correct, so the test should pass at once.
> Do not change production code. Run pylint, pytest (fast unit tests, `-n auto`) and
> mypy, run the formatter, and commit.

## WHERE

`tests/cli/commands/test_verify_exit_codes_github.py`, class `TestGitHubExitCode`

## WHAT

`test_unverifiable_branch_protection_does_not_affect_exit(self) -> None`

The docstring should say why this is safe: every branch-protection row is
`severity="warning"`, `overall_ok` counts only error-severity checks, and
`_compute_exit_code` reads only `github_result["overall_ok"]`.

## HOW

Reuse the module's existing helpers `_claude_ok()` and `_mlflow_not_installed()`.
Call `_compute_exit_code("claude", _claude_ok(), None, _mlflow_not_installed(), github_result=payload)`.

## DATA — payload

```python
row = {
    "ok": None,
    "value": "not verifiable — token lacks Administration: Read",
    "error": "get_protection failed: HTTP 403: Resource not accessible by personal access token",
    "severity": "warning",
}
payload = {
    "token_configured": {"ok": True, "value": "configured (scopes: unknown)", "severity": "error"},
    "repo_accessible": {"ok": True, "value": "accessible", "severity": "error"},
    "branch_protection": dict(row),
    "ci_checks_required": dict(row),
    "strict_mode": dict(row),
    "force_push": dict(row),
    "branch_deletion": dict(row),
    "overall_ok": True,
}
```

## ALGORITHM

```
assert _compute_exit_code(..., github_result=payload) == 0
```

## Commit

`test(verify): lock in exit code 0 for unverifiable branch protection`
