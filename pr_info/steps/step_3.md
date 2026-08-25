# Step 3 — `jenkins_operations/diagnostics.py`

Read [summary.md](summary.md) first.

Pure helpers plus probe functions. Nothing wires them into the error path yet — that is step 4.

## WHERE

- `src/mcp_coder/utils/jenkins_operations/diagnostics.py` (create)
- `tests/utils/jenkins_operations/test_diagnostics.py` (create)
- `tests/utils/jenkins_operations/fixtures/__init__.py` (create, empty)
- `tests/utils/jenkins_operations/fixtures/jenkins_403_access_denied.html` (create)
- `src/mcp_coder/cli/commands/coordinator/core.py` (modify, `:452-456`)
- `.importlinter` (modify, `:334`)

Do **not** add anything to `jenkins_operations/__init__.py`. Callers use direct submodule imports.

## WHAT

```python
DOCS_POINTER = "See docs/repository-setup/jenkins.md"

@dataclass(frozen=True)
class ProbeResult:
    status: int | None      # None => the request never completed
    url: str
    error_text: str | None  # extracted Jenkins error sentence, if any

def job_url_path(job_path: str) -> str: ...
def extract_jenkins_error(body: str) -> str | None: ...
def probe(session: Session, base_url: str, path: str) -> ProbeResult: ...
def diagnose_403(session: Session, base_url: str) -> str: ...
def diagnose_404(session: Session, base_url: str, job_path: str) -> str: ...
```

`diagnose_403` / `diagnose_404` return the **complete** operator-facing sentence — cause, remedy
and `DOCS_POINTER`. The caller only prefixes context.

## HOW

```python
import html as html_lib
import re
from dataclasses import dataclass
from urllib.parse import quote
from requests import RequestException, Session
```

`.importlinter:334` — widen the `requests_library_isolation` ignore. The exemption is per-module,
not per-package, so this module breaks the contract without it:

```
ignore_imports =
    mcp_coder.utils.jenkins_operations.** -> requests
```

(`jenkins_library_isolation` already uses the `.**` form — match it.)

`core.py:452-456` — replace the third copy of the `quote()` conversion:

```python
pipeline_url = jenkins_base_url + job_url_path(repo_config["executor_job_path"])
```

with `from ....utils.jenkins_operations.diagnostics import job_url_path` (match the relative-import
depth used by the neighbouring imports in that file). The existing comment explaining the
`"Tests/mcp-coder-test"` → `"Tests/job/mcp-coder-test"` conversion moves to `job_url_path`'s
docstring.

Module constants: `_PROBE_TIMEOUT = 10` (seconds — must be passed explicitly; `session.get()`
bypasses `Jenkins._request`, and the library's timeout lives on the `Jenkins` object, not the
session) and `_MAX_ERROR_LEN = 200`.

## ALGORITHM

`job_url_path` — returns the **path only**, so `probe(session, base_url, path)` keeps its shape:

```
parts = [p for p in job_path.split("/") if p]
return "/job/" + "/job/".join(quote(p, safe="") for p in parts)
```

`extract_jenkins_error` — tolerant by design; the useful sentence in the observed page sits
*inside* an HTML comment with no closing `</p>`:

```
if not body.strip(): return None
try <p class="error">(.*?) up to </p> | <!-- | <h1..h6 | end-of-string   (DOTALL, IGNORECASE)
else try <h1>(.*?)</h1>
else fall back to the whole body
strip remaining tags, html_lib.unescape, collapse all whitespace to single spaces
return None if empty, else truncate to _MAX_ERROR_LEN with a trailing "..."
```

`probe` — must never raise; a failing probe must not mask the original error:

```
url = f"{base_url}{path}"
try: response = session.get(url, timeout=_PROBE_TIMEOUT)
except RequestException as exc: return ProbeResult(None, url, str(exc))
error_text = None if response.ok else extract_jenkins_error(response.text)
return ProbeResult(response.status_code, url, error_text)
```

`diagnose_403` — probes in order and reports the **first** endpoint that rejects, because
`/crumbIssuer/api/json` was the actual Run-1 failure and nothing in the original message said so:

```
for path in ("/api/json", "/crumbIssuer/api/json"):
    r = probe(session, base_url, path)
    if r.status == 401: return "401 Unauthorized on {path}{detail}. Authentication failed -
                                check username and API token. {DOCS_POINTER}"
    if r.status == 403: return "403 Forbidden on {path}{detail}. The API user is authenticated
                                but not authorized; Jenkins requires Overall/Read for any REST
                                call. Grant it in the global authorization matrix (it cannot be
                                granted per-job). {DOCS_POINTER}"
return "the server rejected the request, but a follow-up probe succeeded - the permission may
        have changed in the meantime. {DOCS_POINTER}"
```

where `detail` is `f' - "{r.error_text}"'` when `error_text` is set, else `""`.

`diagnose_404` — walks ancestors deepest-first and names the deepest **readable** one, narrowing
the search to a single path segment. It must **not** claim the path exists:

```
parts = [p for p in job_path.split("/") if p]
for depth in range(len(parts) - 1, 0, -1):        # skip the leaf: it already 404'd
    if probe(session, base_url, job_url_path("/".join(parts[:depth])) + "/api/json").status == 200:
        return "404 on '{job_path}' - the folder '{parts[:depth] joined}' is readable;
                '{parts[depth]}' under it is not. Either the name is wrong or the API user lacks
                Job/Read on it. Check both. {DOCS_POINTER}"
return "404 on '{job_path}' - no part of that path is readable. Either the path is wrong or the
        API user lacks Job/Read (and possibly Overall/Read). Check both. {DOCS_POINTER}"
```

Rejected deliberately: listing sibling jobs in the readable parent (noisy on large folders), and
confident wording. Jenkins hides unreadable jobs from the parent's listing, so wrong-name and
missing-`Job/Read` are indistinguishable from outside.

## DATA

`ProbeResult(status: int | None, url: str, error_text: str | None)`. `status is None` means the
request never completed (DNS, TLS, connection refused) and `error_text` holds the transport error.

## TESTS (write first)

**The fixture is load-bearing and must be hostile, not tidy** — a clean fixture only tests the
shapes we already thought of, which is exactly how this bug survived. Synthesise
`jenkins_403_access_denied.html` as a realistic ~60-line Jenkins 2.528.3 error page: full
`<!DOCTYPE html>`, `<head>` with stylesheet links, inlined `<svg><symbol>` definitions,
`<template>` blocks, a footer, and critically:

```html
--><h1>Access Denied</h1><p class="error">job_manager is missing the Overall/Read permission<!--
```

— the error sentence wrapped in an HTML comment with **no closing `</p>`**. Include a plausible
CSRF crumb value and the username in the markup so the "never log the raw page above DEBUG"
constraint has something real to protect. Fixed path so a genuine capture can be dropped in later
without touching the tests. (A real page could not be captured: the reachable Jenkins config
points at `localhost:8080` and the service is stopped.)

`test_diagnostics.py`:

- `extract_jenkins_error`
  - the hostile fixture yields exactly `"job_manager is missing the Overall/Read permission"`
  - a well-formed `<p class="error">Foo</p>` yields `"Foo"`
  - HTML entities are unescaped (`&#039;` → `'`)
  - an `<h1>`-only page falls back to the `<h1>` text
  - a page with no recognisable marker returns bounded text (`len <= _MAX_ERROR_LEN + 3`), not the
    whole page
  - `""` and `"   "` return `None`
- `job_url_path` — `"A/B"` → `"/job/A/job/B"`; a segment with a space and a `#` is percent-encoded;
  a leading/trailing `/` is tolerated
- `probe` — 200 gives `error_text is None`; 403 with the fixture body gives the extracted sentence;
  `RequestException` gives `ProbeResult(status=None, error_text=<message>)` and **does not raise**
- `diagnose_403` — `/api/json` 200 + `/crumbIssuer/api/json` 403 names `/crumbIssuer/api/json`
  (the regression guard for the Run-1 misdirection); `/api/json` 403 names `/api/json`; a 401
  says authentication, not authorization; all-200 returns the neutral fallback
- `diagnose_404` — parent 200 / leaf 404 names both the readable folder and the unreadable segment;
  nothing readable returns the no-ancestor message; a single-segment path is handled without an
  index error
- both diagnosis functions always end with `DOCS_POINTER`

Use a `Mock(spec=Session)` with `get.side_effect` keyed by URL. No network.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`.
>
> Implement step 3 test-first. Write the hostile HTML fixture and
> `tests/utils/jenkins_operations/test_diagnostics.py` first, watch them fail, then write
> `src/mcp_coder/utils/jenkins_operations/diagnostics.py`.
>
> The fixture must be genuinely hostile — full doctype, inlined SVG symbol defs, `<template>`
> blocks, a footer, ~60 lines, and the `<p class="error">` sentence wrapped in an HTML comment with
> no closing tag. A tidy fixture defeats the purpose of the step.
>
> Then widen `.importlinter:334` to `mcp_coder.utils.jenkins_operations.** -> requests` and replace
> the `quote()` block at `coordinator/core.py:452-456` with `job_url_path()`.
>
> Do not export anything from `jenkins_operations/__init__.py`. Do not wire `diagnose_*` into
> `client.py` — that is step 4.
>
> Run, with MCP tools only: `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`,
> `mcp__tools-py__run_lint_imports_check`, and `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`.
> Fix everything they report, then `./tools/format_all.sh` and commit as one commit.
