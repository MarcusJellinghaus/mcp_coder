# Step 3 — OpenSSF Scorecard workflow

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 3** exactly as described in
> `pr_info/steps/step_3.md`. Create `.github/workflows/scorecard.yml` from the content below and add
> the related docs lines. Use the action SHAs verbatim. Run the checks listed below, run the
> formatter, and produce exactly one commit.

## Precondition

`docs/repository-setup/github.md` contains a `## README Badges` section (from Step 2) and
`.github/workflows/scorecard.yml` does not exist. If either is not the case, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `.github/workflows/scorecard.yml` (new)
- `docs/repository-setup/github.md` — `## README Badges` section
- `docs/repository-setup/README.md` — *Files Shared With Other Projects* table

## WHAT

### 1. `.github/workflows/scorecard.yml` — full content

```yaml
name: Scorecard supply-chain security

on:
  branch_protection_rule:
  schedule:
    - cron: '30 1 * * 1'
  push:
    branches: [ main ]

permissions: read-all

jobs:
  analysis:
    name: Scorecard analysis
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      id-token: write
      contents: read
      actions: read
    steps:
      - name: Checkout code
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false

      - name: Run analysis
        uses: ossf/scorecard-action@fa7117db83c52d787ae5a89f350999701505d78e # v2.5.0
        with:
          results_file: results.sarif
          results_format: sarif
          publish_results: true

      - name: Upload to code scanning
        uses: github/codeql-action/upload-sarif@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
        with:
          sarif_file: results.sarif
```

Constraints (`publish_results: true`): no top-level `env` / `defaults`; only Scorecard-approved
actions in the job; no `repo_token`; no `pull_request` trigger. Not a required check.

### 2. `docs/repository-setup/github.md`

Append at the end of the `## README Badges` section (after the "Copying `ci.yml`" note):
```markdown
### Scorecard and CodeQL badges

`.github/workflows/scorecard.yml` needs no secrets: it publishes results for the Scorecard badge and
uploads SARIF to code scanning. The CodeQL badge reflects CodeQL default setup (no workflow file).
```

### 3. `docs/repository-setup/README.md`

In *Files Shared With Other Projects*, insert directly after the `.github/dependabot.yml` row:
```markdown
| `.github/workflows/scorecard.yml` | G | No | Yes | — |
```

## HOW

Standalone workflow, no integration with `ci.yml`. Results publish only from the default branch.

## ALGORITHM

```
on push-to-main / weekly / branch_protection_rule:
  checkout (no persisted credentials)
  scorecard-action -> results.sarif, publish to scorecard.dev
  upload-sarif results.sarif -> code scanning
```

## DATA

`results.sarif` (SARIF 2.1.0) — consumed by `upload-sarif` only.

## Verification

- Re-read `scorecard.yml`: three triggers; workflow-level `permissions: read-all`; job scopes exactly
  `security-events: write`, `id-token: write`, `contents: read`, `actions: read`; all three `uses:`
  lines match the SHAs + `# vX.Y.Z` comments in `summary.md`.
- Run `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_pytest_check` (fast unit set
  from CLAUDE.md, with `-n auto`), `mcp__mcp-tools-py__run_mypy_check` — all pass.
- `mcp__mcp-tools-py__run_format_code`, then commit: `ci: add OpenSSF Scorecard workflow`
