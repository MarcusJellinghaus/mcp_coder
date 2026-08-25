# review-plan review log 1

## Round 1 — 2026-08-25
**Findings**:
I'll gather context: knowledge base, the issue and its links, and the plan files.`pr_info/steps/step_1.md:47` — high — eager `self._client._auths[0][1]` in `__init__` raises `TypeError: 'Mock' object is not subscriptable` against the 15 existing `mock_client = Mock()` doubles in `tests/utils/jenkins_operations/test_client.py`; step 1 only plans to update tests mocking `_client.server`, so the step cannot land green as written.
`pr_info/steps/step_6.md:124` — high — credentials taken from `load_config().get("jenkins", {})` bypass the `JENKINS_URL`/`JENKINS_USER`/`JENKINS_TOKEN` env overrides that `get_config_values`/`_get_jenkins_config()` apply, so `verify` skips or probes different credentials than the coordinator actually uses.
`pr_info/steps/step_3.md:117` — high — `diagnose_403`'s all-probes-succeed fallback discards the error sentence already present in the original exception body; a 403 on the build POST (missing `Job/Build`, both probes 200) yields "the permission may have changed in the meantime" instead of the known cause, a confidently wrong diagnosis of the exact Job/Build case the issue describes.
`pr_info/steps/step_3.md:128` — medium — `diagnose_404`'s ancestor walk stops before the root (`range(len(parts)-1, 0, -1)`), so a single-segment `executor_job_path` always returns "no part of that path is readable" — false, since a 404 implies Overall/Read already works.
`pr_info/steps/step_6.md:166` — medium — the hermetic autouse fixture is scoped to `tests/cli/commands/`; `tests/integration/test_verify_llm_integration.py:59` also drives `execute_verify` and asserts exit 0, so it can issue live Jenkins probes and fail on a configured-but-down server.
`pr_info/steps/summary.md:91` — low — "Eager `_auths[0][1]` assignment ... never calls `_maybe_add_auth()`" over-claims: `_auth_resolved` stays `False`, so `_maybe_add_auth()` still runs on the first real request and can still raise under `python-jenkins[kerberos]`; the hazard is avoided for probes only.
`pr_info/steps/step_3.md:14` — low — `.importlinter:334` is the `black_isolation` contract; the `requests_library_isolation` ignore is at `:321`, as the issue states.
`pr_info/steps/step_3.md:59` — low — replacing the `quote()` block at `core.py:452-456` leaves `from urllib.parse import quote` unused at `core.py:11`; removal is not called out and pylint `W0611` is enabled.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_1.md:47, avoid the eager `self._client._auths[0][1]` read in `__init__` (e.g. resolve lazily or guard with a try/except and getattr-based access), and extend the step's test-update scope to cover all 15 `mock_client = Mock()` doubles in tests/utils/jenkins_operations/test_client.py so the step lands green.", 'In pr_info/steps/step_6.md:124, source Jenkins credentials for `verify` from `get_config_values`/`_get_jenkins_config()` instead of `load_config().get("jenkins", {})`, so JENKINS_URL/JENKINS_USER/JENKINS_TOKEN env overrides apply and verify probes the same credentials the coordinator uses.', 'In pr_info/steps/step_3.md:117, change `diagnose_403`\'s all-probes-succeed fallback to preserve and surface the error sentence from the original exception body rather than replacing it with "the permission may have changed in the meantime", so a build-POST 403 with both probes returning 200 still reports the known Job/Build cause.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-08-25
**Findings**:
I'll gather context from the knowledge base, GitHub issues, and plan files.`pr_info/steps/step_6.md:181` — high — the hermetic `_neutral_jenkins_verify` fixture is added only to `tests/cli/commands/conftest.py`, but `tests/integration/test_verify_llm_integration.py:59` also drives `execute_verify` against the real `~/.mcp_coder/config.toml` and asserts `exit_code == 0`; its `llm_integration` marker is not in the step's exclusion list, and the issue's own environment has `[jenkins]` configured against a stopped `localhost:8080`, so step 6 lands red on the dev machine
`pr_info/steps/step_3.md:65` — low — replacing the `quote()` block at `core.py:452-456` leaves `from urllib.parse import quote` unused at `core.py:11` (its only other use); removal is not called out and pylint `W0611` is enabled
`pr_info/steps/step_6.md:61` — low — `_get_jenkins_config()` is not "the same helper `coordinator/core.py` resolves credentials through"; `core.py:143` has its own `get_jenkins_credentials()`. The env-override rationale still holds (both go through `get_config_values`), but the stated justification is factually wrong
`pr_info/steps/step_6.md:101` — low — consuming `client._http` from the CLI layer adds a second `pylint: disable=protected-access` site, contradicting `summary.md:49`'s claim that the two properties confine protected access to one place
`pr_info/steps/summary.md:49` — low — `base_url` does not absorb all `self._client.server` access: `client.py`'s `get_job_status` keeps two direct reads that the step leaves untouched
`pr_info/steps/step_4.md:76` — low — the fixed wording "the queue item was not found" misattributes a `NotFoundException` raised by `get_build_info()` inside the same `try` block, which is a job-path/Job-Read 404, not a queue-item expiry
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
