# Step 1 — `JenkinsClient.get_job_url`

## LLM prompt

> Read `pr_info/steps/summary.md` (section "Job lookup") and this file, then implement Step 1
> only. Write the tests first, then the implementation. Run pylint, mypy and the fast unit tests
> (see `.claude/CLAUDE.md`), run the formatter, and make exactly one commit:
> `feat(jenkins): add JenkinsClient.get_job_url for executor job lookup`.

## WHERE

- `src/mcp_coder/utils/jenkins_operations/client.py` — new method on `JenkinsClient`, placed
  after `get_recent_builds`.
- `tests/utils/jenkins_operations/test_client_job_url.py` — **new** test file.

## WHAT

```python
# No @log_function_call: it logs ERROR with a traceback before re-raising, and a
# wrong executor_job_path must end the coordinator run with one error line.
def get_job_url(self, job_path: str) -> str:
    """Return the URL Jenkins reports for a job.

    The URL is the identity of the job: two spellings of one path resolve to it.

    Raises:
        JenkinsError: For any Jenkins or transport failure (a 404 carries the
            diagnose_404 diagnosis), or when the path is not a job (e.g. a folder).
    """
```

## HOW

- Uses `self._client.get_info(item=..., query="?tree=url,buildable")`, the same pattern as
  `get_recent_builds`. Do **not** use `jenkins.Jenkins.get_job_info` (it turns a 404 into a
  plain `JenkinsException`, losing the `NotFoundException` that triggers `diagnose_404`).
- Item path: `"/".join(f"job/{part}" for part in job_path.split("/") if part)` — the same
  expression `get_recent_builds` uses (unencoded on purpose; `get_info` quotes it).
- Errors: `JenkinsException` → `raise self._wrap_jenkins_error(e, context, job_path=job_path)
  from None`; any other exception → `raise JenkinsError(f"{context}: {e}") from e`
  (mirrors `get_recent_builds`). `context = f"Failed to look up job '{job_path}'"`.
- No decorator.

## ALGORITHM

```
item = job/<a>/job/<b> ...
try: info = get_info(item=item, query="?tree=url,buildable")
except JenkinsException → wrapped JenkinsError (404 → diagnose_404); except Exception → JenkinsError
if "buildable" not in info or not isinstance(info.get("url"), str):
    raise JenkinsError(f"{context}: not a job (a folder or other item); executor_job_path must name a job")
return info["url"]
```

## DATA

- Returns `str`: the job URL as Jenkins reports it, e.g. `"http://jenkins:8080/job/A/job/Executor/"`.

## Tests (write first) — `test_client_job_url.py`

Use `_mock_jenkins`, `_response`, `BASE_URL` from `.conftest` and patch
`mcp_coder.utils.jenkins_operations.client.Jenkins` (as in `test_client_builds.py`).

1. Job found: `get_info` returns `{"url": f"{BASE_URL}/job/A/job/Executor/", "buildable": True}`
   → returns that URL; `get_info` called with `item="job/A/job/Executor"` and
   `query="?tree=url,buildable"`.
2. Leading/trailing/double slashes in the path are tolerated (same item as above).
3. 404: `get_info.side_effect = NotFoundException(...)`, probe of `{BASE_URL}/job/A/api/json`
   returns 200 → `JenkinsError` whose message contains `"Failed to look up job 'A/Missing'"` and
   `"'A' is readable"`; `__cause__ is None`.
4. Folder: `get_info` returns `{"url": ..., "_class": "...Folder"}` without `buildable` →
   `JenkinsError` mentioning "not a job".
5. Transport error (`requests.ConnectionError`) and timeout (`jenkins.TimeoutException`) →
   `JenkinsError` with the context prefix.
6. No log record at ERROR level is emitted by the client on failure (caplog at DEBUG; assert no
   record with `levelno >= logging.ERROR`) — guards against adding `@log_function_call`.
