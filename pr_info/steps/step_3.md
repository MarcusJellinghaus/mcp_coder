# Step 3 — Documentation

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` only.
> Docs only; follow the wording constraints below exactly (they come from issue
> #1374). Make sure the sample output matches what Step 1's code prints. Make exactly
> one commit.

## WHERE

- `docs/repository-setup/github.md` (sections "Token options" and
  "Repo Security Configuration Checks")
- `docs/repository-setup/quality-and-security-checks.md` (line ~125)

## WHAT / HOW (edits)

1. **Fine-grained PAT intro** — replace "which are the ones `mcp-coder verify` probes"
   with wording that the list names the permissions for its own rows (it must not claim
   to list every permission `verify` probes). The list itself is unchanged.
2. **New subsection under the fine-grained PAT option**, titled for
   `check_branch_status` (e.g. "Code scanning alerts (`check_branch_status`)"): grant
   `Code scanning alerts: Read` (`security_events` read). Mark the permission name
   unconfirmed until a live check runs. Code scanning stays out of the list above.
3. **Classic PAT note** —
   - a `repo`-scope token satisfies the *permission-list* checks above (not "all of
     the checks");
   - `security_events` is the scope GitHub associates with code-scanning alerts, not a
     confirmed requirement;
   - the classic scope name is unverified (the live check covers the fine-grained
     permission only);
   - whether `repo` also covers the alerts endpoint is unverified. Do not claim it does.
4. **Sample output block** — change two lines:
   - `Dependabot security    [ERR]  disabled`
   - `Code scanning alerts   [ERR]  scope missing or Advanced Security not enabled`
5. **"Four rows are API-backed" paragraph** — keep its four-item list (no code
   scanning). The no-permission wording becomes: "The rows that read
   `security_and_analysis` and lack Administration: Read show
   `[WARN] not accessible (<reason>)`." Make no claim about the Dependabot alerts row's
   no-permission output.
   Then, after the list, add two separate sentences:
   - code scanning is also API-backed, needs no Administration: Read, but needs
     `security_events` (Code scanning alerts: Read) and Advanced Security;
   - "Without a token, all five API-backed rows (the four above and code scanning) show
     `[WARN] not accessible (repository not accessible)`."
6. **Rewrite the "Code scanning alerts" paragraph** — the row probes whether the token
   can read code-scanning alerts (`GET .../code-scanning/alerts?per_page=1`). It names
   the scope and Advanced Security. Outcomes:
   - `[OK] scope present` — the token can read alerts;
   - `[ERR] scope missing or Advanced Security not enabled` — HTTP 403;
   - `[WARN] scope missing or not configured` — HTTP 404: scope missing; may also mean
     CodeQL is not enabled or has no analysis yet (unconfirmed). Granting the scope does
     not fix a CodeQL-off 404;
   - `[WARN] not accessible (<reason>)` — rate limit, network or other error.
   Then explain the `check_branch_status` skip, covering both forms:
   `[skipped] alerts not checked (403)` and `alerts not checked: 403` inside a clean
   reviews line. 403 → scope missing or Advanced Security not enabled; 404 → scope
   missing, and may also mean CodeQL is not enabled or has no analysis yet
   (unconfirmed).
   Keep the "report-only and exit-neutral" paragraph.
7. **`quality-and-security-checks.md`** — "including the Dependabot rows" → "including
   the Dependabot rows and the code-scanning alerts row" (the phrase spans a line
   break).

## DATA

No code. Every sample line must match the Step 1 output for its state.
