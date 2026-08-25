# Step 4 — `_wrap_jenkins_error` and handler wiring

Read [summary.md](summary.md) first.

The core fix. After this step the HTML is gone from both the message and the traceback.

## WHERE

- `src/mcp_coder/utils/jenkins_operations/client.py` (modify)
- `tests/utils/jenkins_operations/test_client.py` (modify)

## WHAT

```python
def _clean_jenkins_message(text: str) -> str:
    """Reduce a python-jenkins message to its first line plus any extracted error sentence."""

class JenkinsClient:
    def _wrap_jenkins_error(
        self, exc: JenkinsException, context: str, job_path: str | None = None
    ) -> JenkinsError:
        """Compose a clean, diagnosed JenkinsError. Returns it; the caller raises `from None`."""
```

`_wrap_jenkins_error` **returns** the exception rather than raising it, so `from None` stays
visible at the raise site.

## HOW

```python
from jenkins import Jenkins, JenkinsException, NotFoundException
from .diagnostics import diagnose_403, diagnose_404, extract_jenkins_error
```

`start_job` — insert **before** the existing `except HTTPError` branch, which stays untouched and
live for 409 and every other pass-through code:

```python
except JenkinsException as e:
    raise self._wrap_jenkins_error(
        e, f"Failed to start job '{job_path}'", job_path
    ) from None
except HTTPError as e:          # unchanged — 409 etc.
    ...
except Exception as e:          # unchanged
    ...
```

`get_job_status` — one new branch before the existing broad `except Exception`:

```python
except JenkinsException as e:
    raise self._wrap_jenkins_error(
        e, f"Failed to get status for queue_id {queue_id}"
    ) from None
```

No `job_path` is available there, and no `HTTPError` branch is added (see summary — a 409 on a
queue-item lookup is not a real scenario).

One `except JenkinsException` clause suffices in both places: `NotFoundException` is a subclass,
and `_wrap_jenkins_error` must `isinstance`-dispatch anyway to choose 404-vs-403 wording. The
load-bearing ordering constraint — **before** `except HTTPError` — is preserved.

Do **not** add 403/404 entries to `_http_error_hint`; they would be unreachable. See the
deviations table in the summary.

## ALGORITHM

```
_wrap_jenkins_error(exc, context, job_path):
    logger.debug("Raw Jenkins error for %s: %s", context, exc)   # raw page: DEBUG only, once
    if isinstance(exc, NotFoundException):
        detail = diagnose_404(self._http, self.base_url, job_path) if job_path
                 else "404 - the queue item was not found (it may have expired) or is not readable"
    elif (m := _AUTH_FAIL_RE.search(str(exc))) and m.group(1) in ("401", "403"):
        # pass the sentence python-jenkins appended to the message: when every
        # probe succeeds (e.g. Job/Build missing on the executor) it is the only
        # evidence naming the cause, and diagnose_403 must not discard it.
        _, _, body = str(exc).partition("\n")
        detail = diagnose_403(
            self._http, self.base_url, extract_jenkins_error(body) if body else None
        )
    else:
        detail = _clean_jenkins_message(str(exc))    # 500 and everything else
    return JenkinsError(f"{context}: {detail}")
```

with

```python
_AUTH_FAIL_RE = re.compile(r"Possibly authentication failed \[(\d+)\]")
```

matching the literal string python-jenkins builds in `jenkins_request()`.

`_clean_jenkins_message` — splits the first line from the HTML body python-jenkins appends:

```
head, _sep, body = text.partition("\n")
extracted = extract_jenkins_error(body) if body else None
return f'{head} - "{extracted}"' if extracted else head
```

Wrap the whole `_wrap_jenkins_error` body defensively: if a probe or the extraction itself raises,
fall back to `_clean_jenkins_message(str(exc))`. A diagnostic must never replace a real error with
its own stack trace.

## DATA

Returns `JenkinsError` with a single composed message string. No new attributes, no new public
API. `__cause__` is deliberately `None` — losing the python-jenkins frames is accepted; they are
library internals, and keeping them keeps the raw page alive in every traceback.

## TESTS (write first)

Amend `tests/utils/jenkins_operations/test_client.py`:

1. **Replace the one-line payload at `:272`.** `JenkinsException("Job not found")` is what hid the
   bug — against a one-line message the current code looks correct. Feed the step-3 fixture
   instead, in the exact shape python-jenkins produces:
   ```python
   JenkinsException(
       "Error in request. Possibly authentication failed [403]: Forbidden\n" + FIXTURE_HTML
   )
   ```
2. `test_start_job_403_message_contains_no_html` — assert `"<html"`, `"<svg"`, `"<!DOCTYPE"` and
   `"<template"` are all absent from `str(excinfo.value)`, and that the message is a small number
   of lines. **The primary regression guard.**
3. `test_start_job_403_names_failing_endpoint_and_permission` — with probes mocked so `/api/json`
   returns 200 and `/crumbIssuer/api/json` returns 403 + fixture body, assert the message contains
   `/crumbIssuer/api/json`, `"missing the Overall/Read permission"`, `"not authorized"` and
   `"docs/repository-setup/jenkins.md"`.
4. `test_start_job_403_breaks_exception_chain` — `excinfo.value.__cause__ is None`.
5. `test_start_job_404_names_deepest_readable_ancestor` — `NotFoundException` from `build_job`,
   parent probe 200, leaf probe 404; assert both `'Windows-Agents'` and `'Executor'` appear and
   that the wording states the ambiguity (contains `"Check both"`).
6. `test_start_job_403_on_build_reports_original_cause` — a 403-shaped `JenkinsException` whose
   body says `"job_manager is missing the Job/Build permission"`, with **both** probes returning
   200 (the real missing-`Job/Build` shape). Assert the message contains that sentence and does
   **not** claim the permission "may have changed". Guards against the diagnosis throwing away
   the exception body when the probes cannot reproduce the failure.
7. `test_start_job_500_has_no_html_and_no_probe` — a 500-shaped `JenkinsException`; assert the
   extracted sentence is present, no HTML, and `session.get` was never called.
8. `test_get_job_status_404_reports_queue_item` — no `job_path`, so the message mentions the queue
   item and does **not** attempt a path walk.
9. `test_raw_body_logged_only_at_debug` — with `caplog.set_level(logging.DEBUG)` the raw page
   appears exactly once in DEBUG records; at INFO it appears nowhere. The page carries a live CSRF
   crumb and the username.
10. `test_probe_failure_does_not_mask_original_error` — make `session.get` raise; the resulting
    `JenkinsError` still carries a useful message and no traceback from the probe.

**Move the 500 case out of `TestStartJobHttpErrorMessages` (`:467-472`).** That parametrisation
exercises 500 through the `HTTPError` branch, which is unreachable in production — python-jenkins
converts 500 to `JenkinsException`. It passes today only because it mocks `build_job` directly.
Keep 409 there (the genuine pass-through code); 500 is now covered by test 7 above.

Do **not** assert zero tracebacks. `@log_function_call` always logs `ERROR ... exc_info=True` and
is out of scope.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Steps 1-3 must be committed first.
>
> Implement step 4 test-first. Start by replacing the `JenkinsException("Job not found")` payload
> at `tests/utils/jenkins_operations/test_client.py:272` with the step-3 fixture in the exact shape
> python-jenkins produces, add the ten tests described, watch them fail, then add
> `_clean_jenkins_message` and `JenkinsClient._wrap_jenkins_error` and wire the
> `except JenkinsException` branch into `start_job` and `get_job_status`.
>
> The new branch must come **before** the existing `except HTTPError` branch, which stays exactly
> as it is — it is live for 409. Do not add 403/404 entries to `_http_error_hint`: they would be
> unreachable, since python-jenkins converts those codes before they can reach that branch.
>
> Also move the unreachable 500 case out of the `TestStartJobHttpErrorMessages` parametrisation at
> `:467-472`, keeping 409.
>
> Run, with MCP tools only: `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`,
> `mcp__tools-py__run_lint_imports_check`, and `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`.
> Fix everything they report, then `./tools/format_all.sh` and commit as one commit.
