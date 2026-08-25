# Summary — Issue #1114: Jenkins permission errors

Strip Jenkins HTML from console output, diagnose 403/404 with our own probe requests,
and expose a Jenkins permission check in `mcp-coder verify`.

## Problem

A single misconfiguration (the `job_manager` API user missing Jenkins permissions) produced
three unrelated-looking errors, two of which dumped ~60 lines of Jenkins HTML six times per run.

Confirmed against the source:

- `jenkins.Jenkins.jenkins_request()` converts `401/403/500` into
  `JenkinsException(msg + "\n" + response.text)` and `404` into
  `NotFoundException("Requested item could not be found")` **before** they escape the library.
  Everything else (notably `409`) is re-raised as `requests.HTTPError`.
- `client.py:180` catches `HTTPError` — which those converted exceptions are not — so they fall
  through to the broad `except Exception` at `client.py:196`, where `str(e)` **is** the HTML page.
- `raise JenkinsError(...) from e` keeps the raw page alive as `__cause__`, so the HTML also
  renders in every traceback.
- `get_job_status` (`client.py:277`) has only the broad handler — no `HTTPError` branch at all.

## Approach

1. **Catch what is actually raised.** One `except JenkinsException` branch, ordered *before* the
   existing `except HTTPError` branch (which stays live for 409), in both `start_job` and
   `get_job_status`. Shared via `JenkinsClient._wrap_jenkins_error()`.
2. **Break the chain.** `raise ... from None`; raw body logged once at DEBUG.
3. **Diagnose after the fact, never preflight.** On 403/404 issue our own probe requests on
   python-jenkins' own session to name the failing endpoint and the deepest readable ancestor.
   Zero cost on the happy path.
4. **Two `verify` sections** built on the same probe helpers.
5. **`docs/repository-setup/jenkins.md`** with the permission matrix.

## Architectural / design changes

### New module: `mcp_coder/utils/jenkins_operations/diagnostics.py`

Free functions with an **injected `requests.Session`** — no client, no config, no I/O setup of
its own. Separated from `client.py` for cohesion (client.py is 294 lines, well under any limit):
`client.py` owns the python-jenkins lifecycle, `diagnostics.py` owns raw HTTP introspection and
the operator-facing remedy text.

Consumed by two callers that share nothing else: `JenkinsClient._wrap_jenkins_error` (error path)
and `cli/commands/verify_jenkins.py` (verify path).

### New seam: `JenkinsClient.base_url` and `JenkinsClient._http`

Two documented properties confining all protected access to `python-jenkins` internals to one
place, with tests pinning the assumptions. `base_url` also absorbs the existing protected access
at `core.py:449`.

**Probes must share the library's session.** `Jenkins.__init__` configures its session with a
retry adapter, honours `PYTHONHTTPSVERIFY=0` and injects `JENKINS_API_EXTRA_HEADERS`. A probe on
a fresh session inherits none of that and would misreport transport problems (self-signed cert,
proxy header) as permission problems.

**Auth is resolved eagerly in `__init__`, not via `_maybe_add_auth()`.** `Jenkins._session.auth`
is populated lazily on the first request, so a probe on a fresh client would go out anonymous and
misreport a false 401/403. Rather than guard a call to `_maybe_add_auth()` — which issues a live
`GET /api/json` when `requests_kerberos` is installed, and would therefore throw before any probe
runs — `JenkinsClient.__init__` assigns `_session.auth = _auths[0][1]` directly. `_auths[0]` is
unconditionally the basic-auth entry when username and password are supplied (kerberos is
*appended* at index 1), and `JenkinsClient.__init__` already validates both are non-empty. This
removes the hazard instead of guarding it: no network call, no kerberos special case.

### New module: `mcp_coder/cli/commands/verify_jenkins.py`

A deliberate departure from the convention that domain verify functions live in their domain
package: the probes belong to `jenkins_operations`, the section assembly is CLI presentation, and
`verify.py` is already 675 lines against a 750-line repo limit.

A **single** `verify_jenkins()` returns both section dicts. Two functions would read config twice,
construct the client twice, and give tests two mock targets; one function gives one of each.

### Error-message ownership

`diagnose_403()` / `diagnose_404()` return the **complete** diagnosis including remedy and the
docs pointer. `_wrap_jenkins_error` only prefixes the call context. The alternative — a remedy
lookup table in `client.py` — would duplicate text that the diagnosis functions already imply.

No `except JenkinsError` branch is added to the coordinator: `execute_coordinator_run` and
`execute_coordinator_test` are independent paths sharing no error-handling helper, and
`JenkinsClient` is the only seam both cross.

### Deviations from the issue text (deliberate)

| Issue says | Plan does | Why |
|---|---|---|
| Add 403/404 entries to `_http_error_hint` | **Omitted** | `_http_error_hint` is called only from the `except HTTPError` branch, which 403/404 provably never reach (python-jenkins converts them first). The entries would be unreachable code no test can exercise — in the file whose whole failure mode was code that looked right because nothing exercised it. The requirement (403/404 produce good messages) is met by `_wrap_jenkins_error`. |
| Guard `_http` against `python-jenkins[kerberos]` | **Hazard removed** | Eager `_auths[0][1]` assignment in `__init__` never calls `_maybe_add_auth()`, so there is nothing to guard. |
| `except NotFoundException` then `except JenkinsException` | One `except JenkinsException` + `isinstance` dispatch inside `_wrap_jenkins_error` | `NotFoundException` is a subclass, and the helper must isinstance-dispatch anyway to pick 404-vs-403 wording. Two clauses calling the same function is redundant. The load-bearing ordering constraint — **before** `except HTTPError` — is preserved. |
| Shared helper "changes `get_job_status`'s behaviour" | `get_job_status` gets the `JenkinsException` branch only, **no** new `HTTPError` branch | A 409 on a queue-item lookup is not a real scenario; adding the branch adds untestable code. |

## Files created

| Path | Purpose |
|---|---|
| `src/mcp_coder/utils/jenkins_operations/diagnostics.py` | Probe + HTML-extraction + diagnosis free functions |
| `src/mcp_coder/cli/commands/verify_jenkins.py` | `verify_jenkins()` returning both verify section dicts |
| `docs/repository-setup/jenkins.md` | Jenkins permission matrix + troubleshooting |
| `tests/utils/jenkins_operations/fixtures/__init__.py` | Package marker for fixture dir |
| `tests/utils/jenkins_operations/fixtures/jenkins_403_access_denied.html` | Hostile ~60-line synthesised error page |
| `tests/utils/jenkins_operations/test_diagnostics.py` | Tests for `diagnostics.py` |
| `tests/cli/commands/test_verify_jenkins.py` | Tests for `verify_jenkins()` |

## Files modified

| Path | Change |
|---|---|
| `src/mcp_coder/utils/jenkins_operations/client.py` | Eager auth in `__init__`; `base_url` + `_http` properties; `_wrap_jenkins_error`; `except JenkinsException` branch in `start_job` and `get_job_status` |
| `src/mcp_coder/cli/commands/coordinator/core.py` | `:449` protected access → `jenkins_client.base_url`; reuse `job_url_path()` at `:452-456` |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Drop `exc_info=True` at `:160` and `:329` |
| `src/mcp_coder/cli/commands/verify.py` | Call `verify_jenkins()` after GITHUB (`:385`); print two sections; pass `jenkins_ok` |
| `src/mcp_coder/cli/commands/verify_exit_code.py` | New `jenkins_ok: bool \| None` parameter |
| `src/mcp_coder/cli/commands/verify_formatting.py` | Three `_LABEL_MAP` entries |
| `.importlinter` | `requests_library_isolation` ignore widened to `jenkins_operations.**` |
| `docs/repository-setup/README.md` | Register `jenkins.md` in the "Detail Documentation" table |
| `docs/cli-reference.md` | Boy-scout fix at `:505-506` and `:1155-1156` |
| `tests/utils/jenkins_operations/test_client.py` | Replace one-line `JenkinsException("Job not found")` payload with the fixture; move the unreachable 500 case off the `HTTPError` path |
| `tests/cli/commands/conftest.py` | Autouse fixture keeping `execute_verify` hermetic |
| `tests/cli/commands/coordinator/test_commands.py` | Assert `exc_info` is not attached |

## Steps

| # | Step | Commit scope |
|---|---|---|
| 1 | [step_1.md](step_1.md) | `JenkinsClient.base_url` / `_http` / eager auth |
| 2 | [step_2.md](step_2.md) | `docs/repository-setup/jenkins.md` + README registration |
| 3 | [step_3.md](step_3.md) | `diagnostics.py` + `.importlinter` |
| 4 | [step_4.md](step_4.md) | `_wrap_jenkins_error` + handler wiring |
| 5 | [step_5.md](step_5.md) | Drop `exc_info=True` in the coordinator |
| 6 | [step_6.md](step_6.md) | `verify_jenkins.py` + verify wiring + exit code |
| 7 | [step_7.md](step_7.md) | `cli-reference.md` `--dry-run` boy-scout fix |

Steps 1 → 3 → 4 is the load-bearing order: the probes need a correctly authenticated session, or
they report a false 403 — exactly the misdiagnosis this issue exists to eliminate. Step 2 lands
before step 3 so the docs pointer baked into the remedy text is never dangling. Steps 5 and 7 are
independent and may be reordered.

## Acceptance

Without Overall/Read — once, no HTML (`log_function_call` supplies the
`start_job FAILED: JenkinsError: ` prefix):

```
Failed to start job 'Windows-Agents/Executor': 403 Forbidden on /crumbIssuer/api/json -
"job_manager is missing the Overall/Read permission". The API user is authenticated but not
authorized; Jenkins requires Overall/Read for any REST call. Grant it in the global
authorization matrix (it cannot be granted per-job). See docs/repository-setup/jenkins.md
```

Without Job/Read:

```
Failed to start job 'Windows-Agents/Executor': 404 on 'Windows-Agents/Executor' - the folder
'Windows-Agents' is readable; 'Executor' under it is not. Either the name is wrong or the API
user lacks Job/Read on it. Check both. See docs/repository-setup/jenkins.md
```

**Do not write a test asserting zero tracebacks.** `@log_function_call` lives in `mcp-coder-utils`,
always logs `ERROR ... exc_info=True`, and is out of scope. One traceback survives per failure;
`from None` is what stops it from containing the HTML. On the `--dry-run` path
`commands.py:161` re-raises into `main.py:377`, which is deliberately left alone, so `--dry-run`
still emits two tracebacks and `run` emits one.

## Constraints

- **The endpoint URL is unrecoverable from the exception.** `raise JenkinsException(msg)` discards
  `e.response` entirely. Naming `/crumbIssuer/api/json` is only possible by issuing the request
  ourselves — which is why "say which request failed" and "diagnose the cause" are one change.
- **The Jenkins error page contains a live CSRF crumb and the username.** Log only the extracted
  error line; never the raw page above DEBUG. Note `log_function_call` already logs all parameters
  at DEBUG including `start_job`'s `token`, unredacted — pre-existing, but the DEBUG logger is
  already sensitive.
- **HTML extraction must be tolerant.** In the observed page the useful sentence sits *inside* an
  HTML comment with no clean closing `</p>`. Use `re` + `html.unescape` (no new dependency), with a
  truncating fallback when nothing matches.
- **`session.get()` bypasses `Jenkins._request`**, which merges env settings manually. That is
  fine, but the timeout must be passed explicitly — `self.timeout` lives on the `Jenkins` object,
  not on the session.
- **`load_config()` raises `ValueError` on malformed TOML.** `verify_jenkins()` must contain it;
  the CONFIG section already reports that failure.
- **`execute_verify` reads the real `~/.mcp_coder/config.toml`.** On a developer machine with
  `[jenkins]` configured and the server stopped, the new sections would make the existing
  `tests/cli/commands/test_verify*.py` suite fail on a live connection error. Step 6 adds an
  autouse fixture to keep them hermetic.
- **Layering is already correct.** `mcp_coder.cli` sits above `mcp_coder.utils` in the
  `layered_architecture` contract, so `verify_jenkins.py -> jenkins_operations.diagnostics` needs
  no exemption, and `jenkins_library_isolation` already permits `jenkins_operations.** -> jenkins`.
  Only `requests_library_isolation` needs widening (step 3).
- **`coordinator run` is fail-fast by design** — one bad issue stops the run, including remaining
  repos under `--all`. Intentional per the code comment, but stated nowhere an operator sees; the
  `exc_info=True` traceback plus immediate `return 1` is what made it look like a crash.
