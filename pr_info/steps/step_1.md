# Step 1 — `JenkinsClient.base_url` and `_http`

Read [summary.md](summary.md) first.

Creates the single documented seam through which everything later touches `python-jenkins`
internals, and resolves the session auth there so probes are never anonymous.

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
    """python-jenkins' own requests session, with auth resolved on first access."""
```

No change to `__init__` — auth is resolved inside `_http`, not eagerly.

## HOW

```python
from requests import Session  # already-allowed import (requests_library_isolation)
```

`base_url` body (`# pylint: disable=protected-access`):

- `base_url` → `str(self._client.server).rstrip("/")`

`_http` body — resolve auth lazily, and defensively:

```python
# python-jenkins resolves auth lazily inside _maybe_add_auth() on the first
# request. Diagnostic probes (diagnostics.py) reuse this session directly and
# would otherwise go out anonymous and misreport a false 401/403, so resolve it
# here instead. _auths[0] is the basic-auth entry when username and password are
# supplied (kerberos, when installed, is appended at index 1) and both are
# validated non-empty in __init__. Reading it here rather than calling
# _maybe_add_auth() also avoids the live GET /api/json that method issues when
# requests_kerberos is installed.
session = self._client._session
if session.auth is None:
    auths = getattr(self._client, "_auths", None)
    try:
        session.auth = auths[0][1]  # type: ignore[index]
    except (TypeError, IndexError, KeyError):
        # Unexpected python-jenkins internals: probe unauthenticated rather
        # than turning a diagnostic into a crash. Pinned by the tests below.
        logger.debug("Could not resolve python-jenkins session auth")
return session
```

Two reasons this is a property body and not an `__init__` assignment:

- it is only needed on the diagnostic path, so a client that never probes pays nothing;
- an unguarded subscript in `__init__` runs for **every** `JenkinsClient(...)`, including the
  many tests that patch `client.Jenkins` with a plain `Mock()` — `Mock` is not subscriptable, so
  `_auths[0]` would raise `TypeError` at construction time.

The `getattr` + `try/except` keeps that failure mode impossible even if a future python-jenkins
renames or reshapes `_auths`.

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

None beyond the guarded lookup shown above.

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
3. `test_http_session_is_authenticated_on_first_access` — `client._http.auth` is an instance of
   `requests.auth.HTTPBasicAuth`, on a client that has issued no request. **This is the
   regression guard**: it fails if a future python-jenkins reorders `_auths` or changes when auth
   is populated.
4. `test_auth_resolution_makes_no_network_call` — patch `Session.request` (or
   `WrappedSession.request`) to raise `AssertionError`, then construct the client **and read
   `_http`**. Neither may touch the network.
5. `test_http_tolerates_missing_auths` — `delattr`/monkeypatch `_auths` away (or set it to a
   non-subscriptable object) and assert `_http` still returns the session instead of raising.
   Pins the `getattr` + `try/except` guard.

Also add one test asserting `dispatch_workflow` builds its pipeline URL from `base_url` — or, if
that path is already covered in `tests/cli/commands/coordinator/test_core.py`, confirm the
existing test still passes with a `JenkinsClient` (not a bare `Mock`) supplying `base_url`. A
`Mock` client will return a `Mock` for `base_url`, so any existing test mocking
`jenkins_client._client.server` needs updating to set `base_url` instead
(`test_core.py:671` and `:775`).

### Existing `Mock()` doubles in `test_client.py`

`test_client.py` builds its Jenkins double as `mock_client = Mock()` at **15** sites (`:131`,
`:196`, `:215`, `:235`, `:254`, `:270`, `:284`, `:302`, `:327`, `:358`, `:389`, `:420`, `:451`,
`:484`, `:512`). A plain `Mock` supports attribute access but **not** subscripting, so anything
that reaches `_auths[0]` blows up with `TypeError` at that site.

The guarded `_http` above means these tests pass unchanged in this step (`session.auth` on a
`Mock` is a `Mock`, not `None`, so the lookup is skipped). Switch all 15 to `MagicMock()` anyway
as part of this step:

- it makes the doubles subscriptable, so the guard is not silently load-bearing for the suite;
- step 4 routes `start_job`/`get_job_status` failures through `_http`, and those tests need a
  session double that behaves like a mapping-capable mock.

This is a mechanical `Mock()` → `MagicMock()` change (`MagicMock` is already imported in that
file); run the full file afterwards and fix any assertion that depended on `Mock`'s stricter
behaviour.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
>
> Implement step 1 test-first: add `TestJenkinsClientHttpAccess` to
> `tests/utils/jenkins_operations/test_client.py` with the five tests described, watch them fail,
> then add the `base_url` and `_http` properties to `JenkinsClient`, and switch
> `coordinator/core.py:449-451` to `jenkins_client.base_url`.
>
> Auth is resolved lazily inside `_http`, guarded with `getattr` + `try/except` — do **not** add
> an unguarded `self._client._auths[0][1]` assignment to `__init__`; a plain `Mock` is not
> subscriptable and it would break every test that patches `client.Jenkins`.
>
> Do not patch `client.Jenkins` in the new tests — they exist to pin real python-jenkins
> behaviour. Update any existing test that mocks `jenkins_client._client.server`
> (`tests/cli/commands/coordinator/test_core.py:671` and `:775`), and switch all 15
> `mock_client = Mock()` doubles in `test_client.py` to `MagicMock()`.
>
> Then run, with MCP tools only, and fix everything they report:
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`.
>
> Commit as one commit after `./tools/format_all.sh`.
