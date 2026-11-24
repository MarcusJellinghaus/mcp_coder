# Step 6 — Capacity gate and delay in `execute_coordinator_run`

## LLM prompt

> Read `pr_info/steps/summary.md` (section "Coordinator run flow") and this file, then implement
> Step 6 only. Steps 1–5 are done: `JenkinsClient.get_job_url`, `get_dispatch_delay_seconds`,
> `DispatchResult`, `stage_index`/global sort and `find_waiting_build` exist. If any of them is
> missing, write one line to `pr_info/.blocked.txt` naming it and stop. Write the tests first,
> then the implementation. Run pylint, mypy and the fast unit tests (see `.claude/CLAUDE.md`),
> run the formatter, and make exactly one commit:
> `feat(coordinator): gate Jenkins dispatch on executor capacity with a delay between starts`.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/commands.py` — `execute_coordinator_run`, `_Repo`.
- `tests/cli/commands/coordinator/conftest.py` — two autouse fixtures.
- `tests/cli/commands/coordinator/test_commands_capacity_gate.py` — **new** test file.
- Existing run tests: `test_commands.py`, `test_integration.py`, `test_commands_trust_gate.py`,
  `test_commands_dispatch_order.py` — set the Jenkins mock's lookup and build list.

## WHAT

```python
from time import sleep  # module-level name, patched in tests as commands.sleep

from ....utils.jenkins_operations.client import JenkinsClient, JenkinsError
from ....utils.user_config import get_dispatch_delay_seconds
from .core import DispatchResult, find_waiting_build


class _Repo(NamedTuple):
    index: int
    name: str
    full_name: str
    config: dict[str, str]
    issue_manager: IssueManager
    branch_manager: IssueBranchManager
    job_url: str   # blocked-state key, as Jenkins reports it
    job_path: str  # first configured path that resolved to job_url; used for gate checks
```

No new public functions. Gate state is two locals in `execute_coordinator_run`:
`blocked: set[str]` (job URLs) and `pending: _Repo | None` (repo whose job got the last build
and still needs its post-delay re-check).

## HOW

- `delay = get_dispatch_delay_seconds()` right after the config-creation check, inside the outer
  `try` but outside any per-repo/per-issue `except` → a wrong TOML type is a `ValueError` →
  existing `except ValueError` → ERROR line, exit 1.
- Collection loop (per repo, config order), **before** creating `IssueManager` /
  `IssueBranchManager` or fetching issues:
  - `job_urls: dict[str, str]` (path → URL): call `jenkins_client.get_job_url(path)` only for a
    path not seen yet; `job_paths: dict[str, str]` (URL → first path) via `setdefault`.
  - `checked: set[str]`: on the first sight of a URL, `if find_waiting_build(jenkins_client,
    job_paths[url]): blocked.add(url)`.
  - URL in `blocked` → `logger.debug("Skipping repository %s: executor job busy", repo_name)`
    and `continue` (no managers, no fetch, no trust or branch lookups; `--force-refresh`
    changes nothing here).
- Dispatch loop (order per issue — keep it exactly):
  1. `repo.job_url in blocked` → `continue`; no workflow label → existing ERROR + `continue`;
  2. `pending is not None` → `sleep(delay)`; `if find_waiting_build(jenkins_client,
     pending.job_path): blocked.add(pending.job_url)`; `pending = None`; then
     `repo.job_url in blocked` → `continue`;
  3. trust gate (unchanged);
  4. per-issue `try`: `result = dispatch_workflow(...)`;
     `STARTED_LABEL_RATE_LIMITED` → `return 1`; `STARTED` → `pending = repo`;
     cache label update for `STARTED` and `NOT_STARTED` (unchanged).
  - Step 2 runs **outside** the per-issue `try`, so a gate error never becomes
    `Failed processing issue #N`.
- Add a comment above step 2 explaining: the delay must exceed the Jenkins quiet period (a build
  in its quiet period is a queue item, invisible to the gate); no sleep after the last dispatch.
- Outer handler, before `except ValueError`:

```python
except JenkinsError as e:
    # Job lookup or capacity check failed: the message is the diagnosis.
    logger.error("%s", e)
    return 1
```

## ALGORITHM

```
for issue, repo in work:
    if repo.job_url in blocked or no workflow label: continue
    if pending: sleep(delay); if find_waiting_build(client, pending.job_path): blocked.add(pending.job_url)
                pending = None; if repo.job_url in blocked: continue
    trust gate → skipped[repo.name].append(...); continue if untrusted
    result = dispatch_workflow(...); RATE_LIMITED → return 1; STARTED → pending = repo
    cache label update (STARTED or NOT_STARTED)
```

## DATA

- `blocked: set[str]`, `pending: _Repo | None`, `job_urls: dict[str, str]`,
  `job_paths: dict[str, str]`, `checked: set[str]`.

## Tests (write first)

`conftest.py` — autouse fixtures (tests must not sleep or read the real user config):

```python
@pytest.fixture(autouse=True)
def _no_dispatch_sleep() -> Iterator[MagicMock]:
    with patch("mcp_coder.cli.commands.coordinator.commands.sleep") as mock_sleep:
        yield mock_sleep

@pytest.fixture(autouse=True)
def _dispatch_delay() -> Iterator[MagicMock]:
    with patch("mcp_coder.cli.commands.coordinator.commands.get_dispatch_delay_seconds",
               return_value=15) as mock_delay:
        yield mock_delay
```

Existing run tests: set `jenkins.get_job_url.return_value = "https://jenkins.example.com/job/MCP_Coder/job/executor-test/"`
and `jenkins.get_recent_builds.return_value = []` on the patched `JenkinsClient` instance.

`test_commands_capacity_gate.py` (two repos, `get_job_url.side_effect` keyed by path,
`get_recent_builds.side_effect` returning a list per call, `dispatch_workflow` returning
`DispatchResult.STARTED` unless stated; a waiting build is a `BuildInfo` with
`status="running"`, `display_name=f"#{number}"`):

1. Busy job at start → its repo's `IssueManager` is not constructed and
   `get_cached_eligible_issues` is not called for it, also with `force_refresh=True`; the other
   repo (different job URL) dispatches.
2. Two paths resolving to the same URL → one initial `get_recent_builds` call; a busy result
   skips both repos.
3. `get_job_url` is called once per distinct path.
4. Two issues, same job, both started → `sleep` called exactly once with `15`, between the two
   dispatches (no sleep after the last); one re-check `get_recent_builds` call.
5. Re-check finds our build waiting → the second issue of that job is not dispatched and its
   trust gate is not evaluated; later issues of that job are skipped without another sleep.
6. Pending delay, next issue on another free job → sleep, re-check of the **previous** job's path
   (assert the `path=` argument), then the other job's issue is dispatched.
7. `NOT_STARTED` → no sleep and no re-check before the next issue; the cache label update still runs.
8. Untrusted issue between two starts → no extra Jenkins call; the sleep happens once, before the
   next dispatch attempt.
9. `get_dispatch_delay_seconds` returning 30 → `sleep(30)`; raising `ValueError` → exit 1,
   ERROR record, nothing fetched.
10. `get_job_url` raising `JenkinsError("Failed to look up job 'X': 404 ...")` → exit 1, exactly
    one ERROR record from the commands logger with that text, no `exc_info`, no
    "Failed processing issue", no issue fetch.
11. Re-check raising `JenkinsError` → exit 1, ERROR line containing the job path, not
    "Failed processing issue"; untrusted summary still logged.
12. `--repo` mode (`repo="mcp_coder", all=False`) runs the same gate (initial check + skip when busy).
