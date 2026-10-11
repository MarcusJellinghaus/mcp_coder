# Step 3 — Silence PyGithub's `github.GithubRetry` request log

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` using TDD:
> add the test, confirm that it fails, then add the one line. Run pylint, pytest (fast
> unit tests, `-n auto`) and mypy, run the formatter, and commit.

## WHERE

- `tests/utils/test_log_utils_shim.py`, class `TestLogSuppressionShim`
- `src/mcp_coder/utils/log_utils.py`, `setup_logging(log_level: str, log_file: Optional[str] = None) -> None`

## WHAT

### Test (write first), same pattern as `test_httpcore_suppressed_after_setup`

```python
def test_github_retry_suppressed_after_setup(self) -> None:
    """github.GithubRetry should be at WARNING after setup_logging()."""
    setup_logging("DEBUG")
    assert logging.getLogger("github.GithubRetry").level == logging.WARNING
```

### Implementation: add to the `# WARNING level` group

```python
logging.getLogger("github.GithubRetry").setLevel(logging.WARNING)
```

## Rationale

PyGithub's `GithubRetry` logs every 403 at INFO (`Request GET … failed with 403:
Forbidden`) before it decides whether to retry. Logging levels are the calling app's
policy, so the setting belongs in this shim and not in mcp-workspace. The setting also
hides PyGithub's INFO rate-limit backoff lines; the issue accepts that.

## Commit

`fix(logging): silence github.GithubRetry INFO request logs`
