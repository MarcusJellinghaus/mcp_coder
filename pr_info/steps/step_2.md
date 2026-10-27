# Step 2 — `JenkinsClient.get_recent_builds` and `get_console_output`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 2** exactly as described in `pr_info/steps/step_2.md`.
> Use TDD: write `tests/utils/jenkins_operations/test_client_builds.py` first (python-jenkins mocked), then add the two methods to `client.py`.
> Run pylint, the fast pytest set and mypy; all must pass. Then run the formatter and make one commit.

## WHERE

- `src/mcp_coder/utils/jenkins_operations/client.py` — two new methods at the end of `JenkinsClient`.
- `tests/utils/jenkins_operations/test_client_builds.py` — **new**.

## WHAT

```python
@log_function_call
def get_recent_builds(
    self,
    limit: int = 100,
    folder: str | None = None,
    statuses: Collection[str] | None = None,
) -> list[BuildInfo]: ...

def get_console_output(self, job_path: str, build_number: int) -> str: ...   # no @log_function_call
```

Docstring of `get_recent_builds` must state:
- the `tree=` query only reaches `MAX_DEPTH` levels, and deeper jobs are not reported
- `limit` is a window over the newest builds across all jobs; `statuses` filters after truncation
- `limit > 100` switches to `allBuilds`, which may be slow on large servers
- `folder` is the full path from the root; a `folder` that points at a job returns `[]`
- Raises `ValueError` for an unknown status and `JenkinsError` for any Jenkins/transport failure, including a missing folder

## HOW

- New imports in `client.py`:
  - `from collections.abc import Collection`
  - `from requests import Request, Session` (extends the existing `Session` import)
  - `from .builds import build_tree_query, flatten_builds, select_builds, validate_statuses`
  - `job_url_path` added to the existing `.diagnostics` import
  - `BuildInfo` added to the existing `.models` import
- Only the public python-jenkins API is used: `self._client.get_info(item=..., query=...)` and `self._client.jenkins_open(Request(...))`.
- Error handling follows `get_job_status`. `except JenkinsException` → `raise self._wrap_jenkins_error(...) from None`; then `except Exception as e` (same pylint disable comment as the existing methods) → `raise JenkinsError(f"{context}: {e}") from e`.

## ALGORITHM

```
get_recent_builds:
    validate_statuses(statuses)                                   # outside try → ValueError escapes
    item = "/".join(f"job/{p}" for p in folder.split("/") if p) if folder else ""   # unencoded; get_info quotes
    context = f"Failed to list builds in folder '{folder}'" if folder else "Failed to list builds"
    try: tree = self._client.get_info(item=item, query=build_tree_query(limit)); found = flatten_builds(tree)
    except JenkinsException as e: raise self._wrap_jenkins_error(e, context, job_path=folder) from None
    except Exception as e: raise JenkinsError(f"{context}: {e}") from e
    return select_builds(found, limit, statuses)

get_console_output:
    url = f"{self.base_url}{job_url_path(job_path)}/{build_number}/consoleText"   # %2F → %252F
    context = f"Failed to get console output for '{job_path}' #{build_number}"
    try: text = self._client.jenkins_open(Request("GET", url))
    except JenkinsException → _wrap_jenkins_error(e, context, job_path=job_path, build_number=build_number) from None
    except Exception → JenkinsError(f"{context}: {e}") from e
    logger.debug("Fetched console output", extra={"job_path": ..., "build_number": ..., "length": len(text)}); return text
```

## DATA

- `get_recent_builds` → `list[BuildInfo]`, newest first, at most `limit` entries.
- `get_console_output` → the whole log as `str`.

## Tests (`test_client_builds.py`)

Patch `mcp_coder.utils.jenkins_operations.client.Jenkins` and use `_mock_jenkins`, `_response`, `BASE_URL`, `FORBIDDEN_HEAD`, `FIXTURE_HTML` from `.conftest`, as `test_client_errors.py` does.

`get_recent_builds`:
- One `get_info` call with `item=""` and `query=build_tree_query(100)`. The returned tree (two jobs) comes back as `BuildInfo`s, newest first.
- `limit=100` → the query contains `builds[`; `limit=101` → it contains `allBuilds[` (assert on the `query` kwarg; `get_info` is called once).
- `folder="A/B"` → `item="job/A/job/B"`.
- `statuses=["failed"]` → `ValueError`, and `get_info` is not called.
- `statuses=["failure"]` filters after truncation.
- `get_info` raises `NotFoundException` with `folder="A/Missing"`; the probe of `BASE_URL + "/job/A/api/json"` → 200 → `JenkinsError` whose message contains `"'A' is readable"` (`diagnose_404` ran) and has `__cause__ is None`.
- `get_info` raises `JenkinsException(FORBIDDEN_HEAD + "\n" + FIXTURE_HTML)`; the `/api/json` probe → 403 → message contains `"403 Forbidden on /api/json"`.
- `jenkins.TimeoutException("Error in request: timed out")` → `JenkinsError` containing `"timed out"`, with `__cause__ is None` (went through `_wrap_jenkins_error`).
- `requests.ConnectionError("refused")` → `JenkinsError` with `__cause__` being that `ConnectionError` (generic branch).

`get_console_output`:
- `jenkins_open` is called once with a `Request` whose `.method == "GET"` and `.url == BASE_URL + "/job/A/job/mb/job/feature%252Fx/7/consoleText"` for `job_path="A/mb/feature%2Fx"`, `build_number=7`; the text is returned unchanged.
- `NotFoundException` with the job probe (`/job/A/job/B/api/json`) → 200 → message contains `"build #7"` (`diagnose_build_404` ran).
- 403 → `JenkinsError` via `_wrap_jenkins_error`. Timeout → `JenkinsError`. `ConnectionError` → generic branch.
