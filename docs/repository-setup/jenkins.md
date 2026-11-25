# Jenkins Setup

Jenkins-side configuration for the coordinator: API user permissions, credentials, and what to do
when a dispatch fails.

Most Jenkins problems reported against the coordinator are **permission** problems on the API user,
not connectivity problems. Start with the permission matrix below, then use
[Troubleshooting](#troubleshooting) — its subsections are keyed by the error text you actually see.

## Required Permissions

The API user configured in `[jenkins]` (`username` / `api_token`) needs all three:

| Permission | Scope | Why |
|---|---|---|
| `Overall/Read` | **Global** — the top-level authorization matrix | Required for *any* REST call, including `GET /crumbIssuer/api/json`, which happens before the job is ever addressed. **Cannot be granted per-job.** |
| `Job/Read` | The executor job (or a folder above it) | Without it Jenkins returns **404**, not 403, so the job is indistinguishable from a misspelled path. |
| `Job/Build` | The executor job | Required to trigger the build. |

**Where to grant them:**

- `Overall/Read` — *Manage Jenkins → Security → Authorization*, in the global matrix. Adding the
  user to a job's or folder's matrix does **not** grant it.
- `Job/Read` and `Job/Build` — the executor job's *Configure → Enable project-based security*, or
  the matrix of a folder above it (permissions inherit downwards).

If your instance uses Role-Based Strategy or Folder Authorization instead of the matrix plugins,
the permission names are the same; only the place you tick them differs.

## Credentials

Jenkins credentials for mcp-coder are **user-level** configuration in your home directory, not a
project file:

| Platform | Config Path |
|----------|-------------|
| **Linux/macOS** | `~/.mcp_coder/config.toml` |
| **Windows** | `%USERPROFILE%\.mcp_coder\config.toml` |

The `[jenkins]` section holds `server_url`, `username` and `api_token`; `JENKINS_URL`,
`JENKINS_USER` and `JENKINS_TOKEN` override them and take highest priority. See the
[Configuration Guide](../configuration/config.md#jenkins) for the field reference and how to
generate an API token, and its
[Environment Variable Overrides](../configuration/config.md#environment-variable-overrides)
section for the override rules.

Use an **API token**, never the account password. Modern Jenkins instances reject the account
password for REST calls, and the token is revocable on its own without disturbing the account.

The token does **not** exempt the coordinator from CSRF: every dispatch first issues
`GET /crumbIssuer/api/json` to fetch a crumb, which is why a missing `Overall/Read` shows up as a
403 on that endpoint rather than on the job (see [Troubleshooting](#troubleshooting)).

Each coordinator repository additionally names a Jenkins job and a Jenkins credentials ID via
`executor_job_path` and `github_credentials_id` in its `[coordinator.repos.*]` section — also
documented in the [Configuration Guide](../configuration/config.md).

## Verifying the Setup

```bash
mcp-coder verify
```

Two sections cover Jenkins. `JENKINS` checks the server and the API user's global access;
`JENKINS JOBS` checks `Job/Read` on the executor job of every configured coordinator repo:

```
=== JENKINS ================================================================
  Server            [OK] https://jenkins.example.com:8080 reachable
  Authentication    [OK] job_manager (API token valid)
  Overall/Read      [OK] granted

=== JENKINS JOBS ===========================================================
  my-repo           [OK] Windows-Agents/Executor
```

Both sections are skipped when `[jenkins]` is not configured, and `JENKINS JOBS` is skipped when no
`[coordinator.repos.*]` entries exist. A failing row prints the diagnosis and a pointer back to
this file.

**What `verify` cannot tell you:** for a job row it cannot distinguish a *wrong job name* from a
*missing `Job/Read`*. Jenkins deliberately returns 404 for both (see below), so the check reports
the readable folder and the unreadable segment and asks you to check both. Do not read a 404 row as
proof that the name is wrong.

## Troubleshooting

### 403 Forbidden on `/crumbIssuer/api/json`

```
Failed to look up job 'Windows-Agents/Executor': 403 Forbidden on /crumbIssuer/api/json -
"job_manager is missing the Overall/Read permission". The API user is authenticated but not
authorized; Jenkins requires Overall/Read for any REST call. Grant it in the global
authorization matrix (it cannot be granted per-job). See docs/repository-setup/jenkins.md
```

This is **authorization**, not authentication. The token is valid and the user is signed in —
Jenkins knows who they are, which is why the message names them. It refuses the call because
`Overall/Read` is missing.

**Fix:** grant `Overall/Read` in the **global** authorization matrix.

Granting `Job/Build` or `Job/Read` on the executor job does **not** fix this, and it changes
nothing: the crumb request is made against the server root, before any job is addressed, so no
per-job permission is consulted. `Overall/Read` cannot be granted per-job at all.

A 403 that survives after `Overall/Read` is granted is a *different* permission, specific to the
failing request — most often `Job/Build` on the executor job, which fails later, as
`Failed to start job 'Windows-Agents/Executor': 403 ...`. The reported message says so and quotes
the permission Jenkins named.

### 404 on `<job path>`

```
Failed to look up job 'Windows-Agents/Executor': 404 on 'Windows-Agents/Executor' - the folder
'Windows-Agents' is readable; 'Executor' under it is not. Either the name is wrong or the API
user lacks Job/Read on it. Check both. See docs/repository-setup/jenkins.md
```

Jenkins deliberately returns 404 — not 403 — for items the user lacks `Job/Read` on, so that
unauthorized users cannot probe for job names. A job that exists but is invisible to this user and
a job that does not exist are **indistinguishable from outside**. Nothing mcp-coder (or you, via
the REST API as that user) can do will separate them.

**Check both:**

1. **The name.** `executor_job_path` is the path as it appears in the URL, folders included and
   slash-separated: `Windows-Agents/Executor`, not the job's display name. It is case-sensitive.
2. **`Job/Read`.** Grant it on the job, or on a folder above it, for the API user.

The message narrows the search for you: everything up to the named readable folder is fine, so only
the segment named after it is in question. If no folder in the path is readable the message says so
instead — suspect `Overall/Read` first in that case. For a top-level job there is no parent folder
to probe, so the message says only that both the name and `Job/Read` are still open questions.

### `not a job (a folder or other item)`

```
Failed to look up job 'Windows-Agents': not a job (a folder or other item); executor_job_path
must name a job
```

`executor_job_path` names a folder (or a multibranch project) instead of the job inside it. Use the
full path to the job, e.g. `Windows-Agents/Executor`.

### 401 Unauthorized

Authentication failed: the username or API token is wrong, or the token was revoked. Re-check
`username` / `api_token` (and any `JENKINS_USER` / `JENKINS_TOKEN` environment variables, which win
over the config file), and regenerate the token if in doubt.

### Jenkins HTML in the console

Older versions printed the full Jenkins error page. If you still see raw HTML, the extracted error
sentence is on the first line of the message; the raw page is logged only at `DEBUG`. Note that the
page contains a live CSRF crumb and the username — do not paste it into an issue unredacted.

## The Coordinator Is Fail-Fast

`mcp-coder coordinator --all` (and `mcp-coder coordinator --repo NAME`) stops at the **first**
failing issue. It collects the eligible issues of all repositories first and dispatches them from
one global list; the first failure logs the error and ends the run — remaining issues, of any
repository, are not attempted. A rate limit or config error in a later repository ends the run
during collection, before any dispatch.

This is intentional: a Jenkins misconfiguration affects every dispatch equally, and retrying it
once per issue per repo only multiplies the same error. It does mean a single bad issue or a single
permission gap ends the whole run, and that issues already dispatched before the failure **have**
been dispatched — re-running after the fix picks up where it stopped, because dispatched issues
have moved to their next status label.

A failed run ends with a single coordinator error line and exit code 1. The line is one of:

- `Failed to look up job '<path>': ...` — the executor job lookup at run start (wrong path,
  missing `Job/Read` or `Overall/Read`, or a folder instead of a job). No traceback above it.
- `Failed to list builds under '<path>': ...` — the [capacity gate](#executor-capacity-gate)
  could not read the job's builds.
- `Failed processing issue #N: ...` — the dispatch of one issue failed.

No traceback is attached to the error line. One may still appear just above, logged by the
operation that raised (`start_job` and `get_recent_builds` log `... FAILED` with the stack), but it
no longer carries the Jenkins page. Read the error line; that is the diagnosis.
`mcp-coder coordinator --dry-run` differs — it re-raises, so the CLI's top-level error boundary
prints a traceback as well.

## Executor Capacity Gate

The coordinator starts an Executor build only while the executor job has **capacity**: no build
waiting for an agent executor. Without the gate, every eligible issue would get a build at once and
the builds would queue for the agents first-in, first-out, regardless of
[dispatch order](#dispatch-order).

Before every dispatch the coordinator lists the executor job's running builds. A running build
still named `#<number>` is waiting for an agent → that job is **blocked** for the rest of the run
and its issues are skipped; issues of other executor jobs continue in dispatch order. Repositories
whose executor job is busy at run start are not fetched from GitHub at all, also with
`--force-refresh`.

### PR-health inside the gate

[PR-health](../coordinator-vscodeclaude.md#pr-health-checks-for-status-10pr-created) (`status-10` →
`status-71` / `81` / `91`) runs per repo inside the capacity gate, before dispatch. A busy repo still
gets no GitHub call; its PRs are checked on the next run with capacity.

The agent's mcp-coder config needs:

- `[github] trusted_commenters` — accounts whose PR feedback counts (e.g. the machine user);
- a `[github] token` with the PR-health permissions: Actions Read, Code scanning alerts Read, Pull
  requests Read (see [GitHub Setup](github.md)).

### Dependency on the Executor pipeline

The signal is the build's display name, so the gate depends on two things outside this repository:

- the top-level `agent { label 'windows-agent' }` in the Executor job's inline pipeline script
  (AutoRunner `jenkins-windows/README.md`, Step 4 item 7; not version-controlled), and
- `mcpCoderExecutorWindows.groovy` setting `currentBuild.displayName` from `LABEL` at its start,
  i.e. after the agent is allocated.

If the name is ever set before agent allocation (e.g. in a controller-side stage), the gate
silently stops blocking.

The gate reads the build list, not the queue: after the quiet period the build runs on the
controller (library checkout) and waits for the agent as a `PlaceholderTask` that does not reliably
carry the job URL.

### Delay between starts

After a build started, the coordinator waits `[coordinator] dispatch_delay_seconds` (default 15,
see the [Configuration Guide](../configuration/config.md#coordinator)) before the next dispatch,
then re-checks the job that got the build. There is no delay after the last dispatch.

The delay must exceed the Jenkins **quiet period** (5 s by default). A build in its quiet period is
a queue item, not a build, so a shorter delay misses the build just started and dispatches again. A
re-check that comes after the quiet period but before the new build got its agent blocks the job
until the next run — harmless. `buildWithParameters?delay=` is not used for the same reason: a
delayed build sits in the queue, invisible to the gate.

### Side effects

- **Manual Executor builds without `LABEL`** keep `#<number>`: they block the coordinator until they
  finish and, after 60 min, log a WARNING on every run (→ UNSTABLE coordinator build). Accepted:
  they do use an executor.
- **The coordinator holds an agent executor itself** (it runs on `windows-agent`) and its
  `venvLockResource` slot, both also while it sleeps. The waiting build usually gets that executor
  once the coordinator run ends.
- **Run length:** each started build adds one delay before the next dispatch, so a run with a few
  starts exceeds 60 s and the next coordinator build (`disableConcurrentBuilds()`) starts right
  after it. The next run sees the last started build only because its own startup (library
  checkout, agent allocation, Python startup) takes longer than the quiet period.
- **Per-job scope:** blocking is per executor job, while capacity is per agent label. Correct while
  the configured repositories share one executor job; two executor jobs on the same agent label
  would compete first-in, first-out again.

### Dispatch order

One list across all repositories, in reverse pipeline order (closest to done first):

`status-81` → `status-71` → `status-08` → `status-17` → `status-05` → `status-14` → `status-02`

Ties keep the repository order of the config file.

## Related Documentation

- **[Configuration Guide](../configuration/config.md)** — `[jenkins]` and `[coordinator.repos.*]`
  reference
- **[GitHub Setup](github.md)** — tokens, labels, and actions on the GitHub side
- **[CLI Reference](../cli-reference.md)** — `mcp-coder coordinator` and `mcp-coder verify`
