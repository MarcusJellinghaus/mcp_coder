# Step 4 — Integration tests for `get_recent_builds` / `get_console_output`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 4** exactly as described in `pr_info/steps/step_4.md`.
> Add the integration tests to `tests/utils/jenkins_operations/test_integration.py`. They must not use mocks.
> Run pylint, the fast pytest set and mypy. Also run `run_pytest_check(extra_args=["-n", "auto"], markers=["jenkins_integration"])`; those tests must pass, or skip when Jenkins is not configured. Then run the formatter and make one commit.

## WHERE

- `tests/utils/jenkins_operations/test_integration.py` — new test methods in the existing `@pytest.mark.jenkins_integration` class, or in a second marked class. Update the module docstring: the existing lifecycle test does not wait, but the new started-build test waits up to 120 s.

## WHAT

```python
def test_get_recent_builds_returns_sorted_build_infos(self, jenkins_client: JenkinsClient) -> None: ...
def test_started_build_appears_with_console_output(
    self, jenkins_client: JenkinsClient, jenkins_test_setup: dict[str, str]
) -> None: ...
def test_missing_folder_raises_jenkins_error(self, jenkins_client: JenkinsClient) -> None: ...
```

## HOW

- Imports: `time`, `uuid`, `BuildInfo` from `mcp_coder.utils.jenkins_operations.models`, `JenkinsError` from `.client`, and `VALID_STATUSES` from `.builds`.
- Constants at module level: `POLL_INTERVAL_S = 2` and `POLL_TIMEOUT_S = 120`.

## ALGORITHM

```
sorted test: builds = client.get_recent_builds(limit=5)
    assert len <= 5, all BuildInfo, all status in VALID_STATUSES, timestamps non-increasing

started build test:
    queue_id = client.start_job(test_job); deadline = monotonic() + POLL_TIMEOUT_S
    status = client.get_job_status(queue_id)
    while status.status in ("queued", "running"):
        if monotonic() > deadline: pytest.fail(f"Build did not finish within {POLL_TIMEOUT_S}s; last status: {status}")
        time.sleep(POLL_INTERVAL_S); status = client.get_job_status(queue_id)
    parent = test_job.rpartition("/")[0] or None
    match = next((b for b in client.get_recent_builds(folder=parent) if b.job_path == test_job and b.number == status.build_number), None)
    assert match is not None; assert match.status not in ("running", "unknown")
    assert client.get_console_output(match.job_path, match.number).strip()

missing folder test:
    with pytest.raises(JenkinsError): client.get_recent_builds(folder=f"mcp-coder-missing-{uuid.uuid4().hex}")
```

The match uses the default `limit=100`, which leaves room for builds that run concurrently in the same folder.

## DATA

No production code changes.
