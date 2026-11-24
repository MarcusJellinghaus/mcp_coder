# Summary — #1461 coordinator: capacity gate, delay between starts, global reverse-pipeline order

## Goal

`mcp-coder coordinator --all` (AutoRunner cron, every minute) currently starts a Jenkins Executor
build for every eligible issue at once, repo by repo. After this change it:

1. collects the eligible issues of all repos into **one list**, sorted by stage in **reverse
   pipeline order** (closest to done first): 81 → 71 → 08 → 17 → 05 → 14 → 02, ties by config
   repo order, then existing order (stable sort);
2. starts a build only when the executor job has **capacity**: no running build still named
   `#<number>` (= not yet renamed from `LABEL` = still waiting for an agent executor);
3. waits `[coordinator] dispatch_delay_seconds` (default 15) **before the next dispatch** after a
   build started, then re-checks the job that got that build — never after the last one;
4. skips repos whose executor job is busy **before touching GitHub** (no fetch, no trust or
   branch lookups; `--force-refresh` does not override).

The full requirements are in issue #1461; this plan implements them as written.

## Architectural / design changes

### Coordinator run flow (`commands.py: execute_coordinator_run`)

Before: `for repo: fetch → per-repo sort → for issue: trust gate → dispatch`.

After — two loops, no new classes:

```
delay = get_dispatch_delay_seconds()                 # once, at run start
# Collection loop (config order)
for index, repo_name in enumerate(repo_names):
    validate config; url = job URL of its path (get_job_url once per distinct path)
    first time this URL is seen: if find_waiting_build(client, path): blocked.add(url)
    if url in blocked: skip repo (no IssueManager, no fetch)
    else: fetch eligible issues → work += [(issue, _Repo(...)) ...]
work.sort(key=lambda item: (stage_index(item[0]), item[1].index))
# Dispatch loop
pending: _Repo | None = None
for issue, repo in work:
    skip if repo.job_url in blocked (or no workflow label)
    if pending: sleep(delay); re-check pending's job → maybe blocked; pending = None; skip if now blocked
    trust gate → dispatch_workflow → STARTED: pending = repo
```

- **Gate state = two local variables**: `blocked: set[str]` (job URLs) and `pending: _Repo | None`.
  A job's result is only invalidated by a start, and the next dispatch attempt always re-checks
  that job after the sleep, so "not in `blocked`" *is* the cached result. No gate class, no cache.
- **Blocking is per executor job**, keyed by the job URL Jenkins reports (`get_job_url`), so two
  spellings of one path share a key. Each distinct `executor_job_path` is resolved once per run.
- **Per-repo context** is a private `_Repo` NamedTuple (index, name, full_name, config, managers,
  job_url, job_path). Work items are `(issue, _Repo)` tuples.
- **Sort key** is a tuple `(stage_index, repo_index)` so more criteria can be added later.
  The per-repo sorts in `core.py` are removed; the global sort is the only one.
- **Untrusted summary** is collected per repo (`dict[str, list]`) and logged in one `finally`
  at the end of the run (also when the run ends early).
- **Errors**: `JenkinsError` (job lookup, gate check) is caught explicitly in `commands.py` → one
  ERROR line, exit 1 (today it reaches `except Exception` → re-raise → exit 2). Gate checks run
  outside the per-issue `try`, so they never become `Failed processing issue #N`.
- **Sleep** is imported as `from time import sleep` in `commands.py`, so tests patch
  `commands.sleep` without touching `time.sleep` globally.

### `dispatch_workflow` result (`core.py`)

`bool` → `DispatchResult` enum: `STARTED`, `NOT_STARTED` (no linked branch / invalid repo URL),
`STARTED_LABEL_RATE_LIMITED` (today's `False`). Only `STARTED` sets the pending delay. The cache
label write after `NOT_STARTED` stays as today.

### Capacity signal (`core.py: find_waiting_build`)

Lists the executor job's running builds via `JenkinsClient.get_recent_builds(path=..., statuses=
["running"])` (default `limit` 100 — `select_builds` applies `limit` before the status filter).
A running build whose `display_name` is `""` or `#<number>` is waiting. Logs one INFO naming the
waiting build, and a neutral WARNING for any such build unnamed for more than 60 min (fixed).
Depends on the Executor pipeline renaming the build only after it holds an agent executor —
documented next to the check and in `docs/repository-setup/jenkins.md`.

### Job lookup (`client.py: JenkinsClient.get_job_url`)

`get_info(item, query="?tree=url,buildable")`, keeps python-jenkins' `NotFoundException` so a
wrong path gets the `diagnose_404` diagnosis via `_wrap_jenkins_error`. A response without
`buildable` (folder, multibranch, root) → `JenkinsError`. All other exceptions → `JenkinsError`.
**Not** decorated with `@log_function_call` (it would log an ERROR traceback before re-raising).

### Configuration (`user_config.py`)

`[coordinator] dispatch_delay_seconds: FieldDef(int)` in `_CONFIG_SCHEMA` (so `verify` doesn't
warn about an unknown key) and `get_dispatch_delay_seconds()`: unset → 15; integer ≤ 0 → WARNING,
15; wrong TOML type → `ValueError` from the schema check in `get_config_values` → ERROR, exit 1.

### Priority order (`command_templates.py`)

`PRIORITY_ORDER` becomes 81 → 71 → 08 → 17 → 05 → 14 → 02 (adds the missing 71/81), with a new
comment. A new `core.stage_index(issue)` replaces the two duplicated inner `get_priority` helpers.

## Files created or modified

### Source (modified)

| File | Change |
|---|---|
| `src/mcp_coder/utils/jenkins_operations/client.py` | New `JenkinsClient.get_job_url(job_path)` |
| `src/mcp_coder/utils/user_config.py` | Schema entry + `get_dispatch_delay_seconds()` |
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | New `PRIORITY_ORDER` and comment |
| `src/mcp_coder/cli/commands/coordinator/core.py` | `DispatchResult`, `stage_index`, `find_waiting_build`; per-repo sorts removed; docstrings |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Collect → global sort → gated dispatch loop with delay; `except JenkinsError` |
| `src/mcp_coder/cli/commands/coordinator/__init__.py` | Export `DispatchResult` |

### Tests

| File | Change |
|---|---|
| `tests/utils/jenkins_operations/test_client_job_url.py` | **New** — `get_job_url` |
| `tests/utils/test_user_config_dispatch_delay.py` | **New** — `get_dispatch_delay_seconds` |
| `tests/cli/commands/coordinator/test_core_dispatch.py` | Expect `DispatchResult` values |
| `tests/cli/commands/coordinator/test_core_eligibility.py` | No per-repo sort; `stage_index` tests |
| `tests/cli/commands/coordinator/test_core_capacity.py` | **New** — `find_waiting_build` |
| `tests/cli/commands/coordinator/test_commands_dispatch_order.py` | **New** — global order, summary at end |
| `tests/cli/commands/coordinator/test_commands_capacity_gate.py` | **New** — gate, delay, busy-repo skip, errors |
| `tests/cli/commands/coordinator/conftest.py` | Autouse: patch `commands.sleep` and `commands.get_dispatch_delay_seconds` |
| `tests/cli/commands/coordinator/test_commands.py`, `test_integration.py`, `test_commands_trust_gate.py` | `dispatch_workflow` mocks return `DispatchResult.STARTED`; Jenkins mock sets `get_job_url` / `get_recent_builds` |

### Docs (modified)

`docs/repository-setup/jenkins.md`, `docs/repository-setup/github.md`, `docs/cli-reference.md`,
`docs/configuration/config.md`, `docs/architecture/architecture.md`.

No new source modules or packages.

## Steps

1. `JenkinsClient.get_job_url` — [step_1.md](step_1.md)
2. `[coordinator] dispatch_delay_seconds` config — [step_2.md](step_2.md)
3. `DispatchResult` from `dispatch_workflow` — [step_3.md](step_3.md)
4. Global reverse-pipeline order (collect, then sort) — [step_4.md](step_4.md)
5. `find_waiting_build` capacity signal — [step_5.md](step_5.md)
6. Capacity gate and delay in `execute_coordinator_run` — [step_6.md](step_6.md)
7. Documentation — [step_7.md](step_7.md)
