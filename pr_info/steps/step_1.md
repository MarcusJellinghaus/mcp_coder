# Step 1 — `JenkinsClient.base_url`, `_http`, and eager auth resolution

Read [summary.md](summary.md) first.

Creates the single documented seam through which everything later touches `python-jenkins`
internals, and eliminates the lazy-auth hazard at the root.

## WHERE

- `src/mcp_coder/utils/jenkins_operations/client.py` (modify)
- `src/mcp_coder/cli/commands/coordinator/core.py` (modify, `:449-451`)
- `tests/utils/jenkins_operations/test_client.py` (modify — add one test class)

## WHAT

Two properties on `JenkinsClient`:

```python
@property
def base_url(self) -> str:
    """Jenkins server URL with no trailing slash."""

@property
def _http(self) -> Session:
    """python-jenkins' own pre-authenticated requests session."""
```

Plus one assignment at the end of `__init__`.

## HOW

```python
from requests import Session  # already-allowed import (requests_library_isolation)
```

At the end of `__init__`, immediately after `self._client = Jenkins(...)`:

```python
# python-jenkins resolves auth lazily inside _maybe_add_auth() on the first
# request. Diagnostic probes (diagnostics.py) reuse this session directly and
# would otherwise go out anonymous and misreport a false 401/403. _auths[0] is
# always the basic-auth entry when username and password are supplied (kerberos,
# when installed, is appended at index 1), and both are validated non-empty
# above — so this assignment is exact and needs no guard. Assigning directly
# rather than calling _maybe_add_auth() also avoids the live GET /api/json that
# method issues when requests_kerberos is installed.
self._client._session.auth = (  # pylint: disable=protected-access
    self._client._auths[0][1]
)
```

Property bodies (each needs `# pylint: disable=protected-access`):

- `base_url` → `str(self._client.server).rstrip("/")`
- `_http` → `self._client._session`

`_http`'s docstring must state *why* the session is shared: it carries the retry adapter,
`PYTHONHTTPSVERIFY` handling and `JENKINS_API_EXTRA_HEADERS` configured by `Jenkins.__init__`;
a probe on a fresh session would misreport transport problems as permission problems.

Then in `core.py`, replace `:449-451`:

```python
jenkins_base_url = jenkins_client.base_url
```

deleting the now-redundant `# pylint: disable=protected-access` comment there. Leave `:452-456`
alone in this step — step 3 replaces it with `job_url_path()`.

## ALGORITHM

None — three assignments.

## DATA

- `base_url` → `str`, e.g. `"http://jenkins:8080"` (input `"http://jenkins:8080/"`;
  `Jenkins.__init__` always appends a trailing slash to `server`).
- `_http` → `requests.Session` with `.auth` set to a `requests.auth.HTTPBasicAuth`.

## TESTS (write first)

New class `TestJenkinsClientHttpAccess` in `tests/utils/jenkins_operations/test_client.py`.

These tests must **not** patch `client.Jenkins` — a `Mock` would make the library assumptions
untestable, and pinning those assumptions is the entire point. Constructing a real `Jenkins`
object performs no network I/O (verified in `Jenkins.__init__`).

1. `test_base_url_strips_trailing_slash` — construct with `"http://jenkins:8080"` and with
   `"http://jenkins:8080/"`; both yield `"http://jenkins:8080"`.
2. `test_http_session_is_the_library_session` — `client._http is client._client._session`.
3. `test_http_session_is_authenticated_before_any_request` — `client._http.auth` is an
   instance of `requests.auth.HTTPBasicAuth`. **This is the regression guard**: it fails if a
   future python-jenkins reorders `_auths` or changes when auth is populated.
4. `test_auth_resolution_makes_no_network_call` — patch `Session.request` (or
   `WrappedSession.request`) to raise `AssertionError`, then construct the client. Constructing
   must not touch the network.

Also add one test asserting `dispatch_workflow` builds its pipeline URL from `base_url` — or, if
that path is already covered in `tests/cli/commands/coordinator/test_core.py`, confirm the
existing test still passes with a `JenkinsClient` (not a bare `Mock`) supplying `base_url`. A
`Mock` client will return a `Mock` for `base_url`, so any existing test mocking
`jenkins_client._client.server` needs updating to set `base_url` instead.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
>
> Implement step 1 test-first: add `TestJenkinsClientHttpAccess` to
> `tests/utils/jenkins_operations/test_client.py` with the four tests described, watch them fail,
> then add the `base_url` and `_http` properties plus the eager auth assignment to
> `JenkinsClient`, and switch `coordinator/core.py:449-451` to `jenkins_client.base_url`.
>
> Do not patch `client.Jenkins` in the new tests — they exist to pin real python-jenkins
> behaviour. Update any existing test that mocks `jenkins_client._client.server`.
>
> Then run, with MCP tools only, and fix everything they report:
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`.
>
> Commit as one commit after `./tools/format_all.sh`.
