# Step 2 — `docs/repository-setup/jenkins.md`

Read [summary.md](summary.md) first.

Docs-only, no code, no tests. Lands **before** step 3 so the `See docs/repository-setup/jenkins.md`
pointer baked into the remedy text (step 3) and into verify's `install_hint` (step 6) is never
dangling.

## WHERE

- `docs/repository-setup/jenkins.md` (create)
- `docs/repository-setup/README.md` (modify — one table row)

## WHAT

A troubleshooting-oriented setup doc. The operator arriving here has a broken run and an error
message; lead with the permission matrix, not with prose.

Required content:

**1. Permission matrix.** The table an operator can act on directly:

| Permission | Scope | Why |
|---|---|---|
| `Overall/Read` | **Global** — the top-level authorization matrix | Required for *any* REST call, including `GET /crumbIssuer/api/json`, which happens before the job is ever addressed. **Cannot be granted per-job.** |
| `Job/Read` | The executor job (or a folder above it) | Without it Jenkins returns **404**, not 403, so the job is indistinguishable from a misspelled path. |
| `Job/Build` | The executor job | Required to trigger the build. |

**2. Credential configuration.** Point at `docs/configuration/config.md` for the `[jenkins]`
section (`server_url`, `username`, `api_token`) and the `JENKINS_URL` / `JENKINS_USER` /
`JENKINS_TOKEN` overrides. Do not restate the schema — link it.

**3. Verifying the setup.** `mcp-coder verify` and its `JENKINS` / `JENKINS JOBS` sections
(added in step 6). Show the expected passing output.

**4. Troubleshooting.** One subsection per symptom, keyed by the message the operator actually
sees, so a web search or Ctrl-F on the error text lands here:

- *403 Forbidden on `/crumbIssuer/api/json`* — authorization, **not** authentication. The token
  is fine; the user is signed in. Grant `Overall/Read` globally. Note explicitly that granting
  `Job/Build` on the executor does **not** fix this — it was the natural first response and it
  changes nothing.
- *404 on `<job path>`* — Jenkins deliberately returns 404 for items the user lacks `Job/Read`
  on, so unauthorized users cannot probe for job names. Wrong name and missing `Job/Read` are
  indistinguishable from outside. Check both.

**5. A note that `coordinator run` is fail-fast** — the first failing issue aborts the run,
including remaining repos under `--all`. This is intentional but currently documented nowhere an
operator sees.

Do **not** claim `mcp-coder verify` can distinguish a wrong job name from a missing `Job/Read`.
It cannot, Jenkins makes it impossible, and a confidently wrong diagnosis is the original failure
mode this issue exists to fix.

## HOW

Register in `docs/repository-setup/README.md`, in the **first** table ("Detail Documentation",
columns `| Topic | File | Applies to |`) — *not* the second table ("Files Shared With Other
Projects"). Follow the `agent-permissions.md` row as the model. Place it after the `github.md`
row (both are external-service setup).

Suggested row:

```
| Jenkins: API user permissions, credentials, coordinator job setup | [jenkins.md](jenkins.md) | Repos dispatched by the coordinator |
```

Nothing Jenkins-related exists under `docs/repository-setup/` today; the only current Jenkins docs
are the `[jenkins]` credentials in `docs/configuration/config.md`.

## ALGORITHM / DATA

N/A.

## TESTS

None — docs only. `tests/cli/commands/test_check_file_sizes.py` and any link checker still need to
pass, so keep the file under the 750-line limit (it will be nowhere near) and make sure every
relative link resolves.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.
>
> Write `docs/repository-setup/jenkins.md` covering the five required sections, and register it in
> the first table of `docs/repository-setup/README.md` following the `agent-permissions.md` row as
> a model.
>
> Match the tone and structure of the existing `docs/repository-setup/github.md` — read it first.
> Verify every relative link resolves to a real file.
>
> This step touches no Python. Run `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
> to confirm nothing regressed, then commit as one commit.
