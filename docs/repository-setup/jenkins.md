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
Failed to start job 'Windows-Agents/Executor': 403 Forbidden on /crumbIssuer/api/json -
"job_manager is missing the Overall/Read permission". The API user is authenticated but not
authorized; Jenkins requires Overall/Read for any REST call. Grant it in the global
authorization matrix (it cannot be granted per-job). See docs/repository-setup/jenkins.md
```

This is **authorization**, not authentication. The token is valid and the user is signed in —
Jenkins knows who they are, which is why the message names them. It refuses the call because
`Overall/Read` is missing.

**Fix:** grant `Overall/Read` in the **global** authorization matrix.

Granting `Job/Build` on the executor job does **not** fix this. It is the natural first response —
the failing operation is a build trigger — and it changes nothing: the crumb request is made
against the server root, before any job is addressed, so no per-job permission is consulted.
`Overall/Read` cannot be granted per-job at all.

A 403 that survives after `Overall/Read` is granted is a *different* permission, specific to the
failing request — most often `Job/Build` on the executor job. The reported message says so and
quotes the permission Jenkins named.

### 404 on `<job path>`

```
Failed to start job 'Windows-Agents/Executor': 404 on 'Windows-Agents/Executor' - the folder
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
failing issue. It logs the error and returns immediately — remaining issues in that repository are
not attempted, and under `--all` neither are the remaining repositories.

This is intentional: a Jenkins misconfiguration affects every dispatch equally, and retrying it
once per issue per repo only multiplies the same error. It does mean a single bad issue or a single
permission gap ends the whole run, and that issues already dispatched before the failure **have**
been dispatched — re-running after the fix picks up where it stopped, because dispatched issues
have moved to their next status label.

A failed run prints a traceback along with the error message. That is the normal fail-fast path,
not a crash: read the error line above it.

## Related Documentation

- **[Configuration Guide](../configuration/config.md)** — `[jenkins]` and `[coordinator.repos.*]`
  reference
- **[GitHub Setup](github.md)** — tokens, labels, and actions on the GitHub side
- **[CLI Reference](../cli-reference.md)** — `mcp-coder coordinator` and `mcp-coder verify`
