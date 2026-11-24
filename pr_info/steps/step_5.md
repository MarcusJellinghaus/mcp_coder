# Step 5 — `find_waiting_build` capacity signal

## LLM prompt

> Read `pr_info/steps/summary.md` (section "Capacity signal") and this file, then implement
> Step 5 only. Write the tests first, then the implementation. Run pylint, mypy and the fast
> unit tests (see `.claude/CLAUDE.md`), run the formatter, and make exactly one commit:
> `feat(coordinator): detect executor builds still waiting for an agent`.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/core.py` — new function `find_waiting_build` and
  constant `UNNAMED_WARNING_AFTER`, placed after `build_jenkins_label`.
- `tests/cli/commands/coordinator/test_core_capacity.py` — **new** test file.

## WHAT

```python
UNNAMED_WARNING_AFTER = timedelta(minutes=60)


def find_waiting_build(jenkins_client: JenkinsClient, job_path: str) -> BuildInfo | None:
    """Return a running build of the executor job that is still waiting for an agent.

    The signal is the display name: the Executor pipeline sets currentBuild.displayName
    from LABEL right after it gets its agent executor (top-level ``agent`` in the
    Executor job's pipeline script), so a running build still named ``#<number>`` is
    waiting. If the pipeline ever renames before agent allocation, this check silently
    stops blocking. See docs/repository-setup/jenkins.md.

    Returns:
        The oldest waiting build, or None when the job has capacity.

    Raises:
        JenkinsError: If the build list cannot be read.
    """
```

## HOW

- Imports in `core.py`: `from datetime import UTC, datetime, timedelta`,
  `from ....utils.jenkins_operations.models import BuildInfo`.
- Calls `jenkins_client.get_recent_builds(path=job_path, statuses=["running"])` — keep the
  default `limit` (100): `select_builds` applies `limit` before the status filter, so a small
  limit could miss a long-running unnamed build. Do not catch `JenkinsError`.
- Logs (module logger of `core.py`):
  - WARNING per waiting build older than 60 min (`now - build.timestamp`), neutral wording:
    `"Executor job '%s': build #%d still unnamed after %d min: waiting for an agent, or a manual build without LABEL (%s)"`.
  - INFO when a waiting build is found:
    `"Executor job '%s' busy: build #%d is waiting for an agent (%s)"`.
  - Never ERROR.

## ALGORITHM

```
builds = jenkins_client.get_recent_builds(path=job_path, statuses=["running"])
waiting = [b for b in builds if b.display_name in ("", f"#{b.number}")]
now = datetime.now(UTC)
for b in waiting: if now - b.timestamp > UNNAMED_WARNING_AFTER: logger.warning(...)
if not waiting: return None
oldest = waiting[-1]  # builds are newest first; logger.info(...); return oldest
```

## DATA

- Returns `BuildInfo | None` (`BuildInfo` from `utils/jenkins_operations/models.py`).

## Tests (write first) — `test_core_capacity.py`

Use a `MagicMock` Jenkins client with `get_recent_builds.return_value` set to `BuildInfo`
objects (helper `_build(number, display_name, minutes_ago)` with
`timestamp=datetime.now(UTC) - timedelta(minutes=minutes_ago)`, `status="running"`).

1. No running builds → `None`; called with `path=job_path, statuses=["running"]` and no `limit`.
2. All running builds renamed (`"mcp_coder - #12 - implement"`) → `None`, no INFO.
3. One build named `"#42"` → returned; one INFO containing `#42` and the job path.
4. Empty display name counts as waiting.
5. Two waiting builds (newest first) → the oldest is returned.
6. Waiting build 61 min old → one WARNING containing "still unnamed after" and
   "manual build without LABEL"; 59 min → no WARNING. No record is ERROR.
7. `get_recent_builds` raising `JenkinsError` → propagates unchanged.
