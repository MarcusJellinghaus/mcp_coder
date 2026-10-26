# Step 2 — Coverage badge in `ci.yml` + `README Badges` docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 2** exactly as described in
> `pr_info/steps/step_2.md`. Extend the `coverage` job in `.github/workflows/ci.yml` to publish the
> combined coverage total to the shared gist, and document the badge setup in
> `docs/repository-setup/github.md` and `docs/repository-setup/README.md`. Use the action SHA and
> names verbatim. Run the checks listed below, run the formatter, and produce exactly one commit.

## Precondition

`.github/workflows/ci.yml` has a `coverage` job containing a step named `Combine coverage data`
followed by `Run diff-cover`. If not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `.github/workflows/ci.yml` — `coverage` job only
- `docs/repository-setup/github.md` — intro line + new section
- `docs/repository-setup/README.md` — two table rows

## WHAT

### 1. `ci.yml` — `coverage` job

Replace the `Combine coverage data` step with (adds `id` and one line; still unconditional):
```yaml
      - name: Combine coverage data
        id: coverage_combine
        run: |
          coverage combine coverage-data
          coverage xml -o coverage.xml
          echo "total=$(coverage report --format=total)" >> "$GITHUB_OUTPUT"
```
Insert directly after it (before `Run diff-cover`):
```yaml
      - name: Update coverage badge
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        continue-on-error: true
        uses: schneegans/dynamic-badges-action@28b0fa8bdeb46170ac397105ece0c1fe58f68910 # v1.9.0
        with:
          auth: ${{ secrets.BADGE_GIST_TOKEN }}
          gistID: ${{ vars.BADGE_GIST_ID }}
          filename: mcp_coder-coverage.json
          label: coverage
          message: ${{ steps.coverage_combine.outputs.total }}%
          color: blue
```
No other `ci.yml` change: no `permissions` change, no new jobs, no renames, `architecture` untouched.

### 2. `docs/repository-setup/github.md`

- Line 3 intro: `GitHub-side configuration: tokens, labels, actions, CI, and automated dependency management.`
  → `GitHub-side configuration: tokens, labels, actions, CI, badges, and automated dependency management.`
- Insert a new section between the end of `## Code Quality CI` (after `### Monitor CI Results`)
  and `## Automated Dependency Management`. Short bullet list:

```markdown
## README Badges

The README shows CI, PyPI, Python, license, static tool badges, a live coverage badge, OpenSSF
Scorecard and CodeQL. Only the coverage badge needs setup.

### Coverage badge

The `coverage` job in `ci.yml` writes the combined coverage total to a public gist on every push to
`main`; shields.io renders it from the gist's raw URL. The write step is `continue-on-error`, so a
broken token never fails CI — the badge just stops updating.

One-time setup (repo owner):

- **Gist:** one public gist shared by all repos, one file per repo named `<repo>-coverage.json`
  (here `mcp_coder-coverage.json`). Placeholder content:
  `{"schemaVersion": 1, "label": "coverage", "message": "pending", "color": "lightgrey"}`
- **Token:** fine-grained PAT with account permission **Gists: read and write** only; repository
  access "Public repositories" (read-only — the minimum GitHub offers); no expiration.
- **Repo secret** `BADGE_GIST_TOKEN` = the PAT. **Repo variable** `BADGE_GIST_ID` = the gist ID.

Rotation: replace the PAT and update `BADGE_GIST_TOKEN` if the token leaks. If it is ever replaced
by an expiring token, the badge silently stops updating on expiry.

> **Copying `ci.yml` to another repo:** rename `filename:` in the `Update coverage badge` step to
> that repo's own `<repo>-coverage.json`. The gist is shared — an unrenamed copy overwrites
> `mcp_coder`'s badge.
```

### 3. `docs/repository-setup/README.md`

- *Detail Documentation* table, `github.md` row: `GitHub-side: tokens, labels, actions, CI, dependabot`
  → `GitHub-side: tokens, labels, actions, CI, badges, dependabot`
- *Files Shared With Other Projects* table, `ci.yml` row, *What to adjust*:
  `Python version, package name, test paths`
  → ``Python version, package name, test paths, coverage badge filename (`<repo>-coverage.json`)``

## HOW

The badge step reads `steps.coverage_combine.outputs.total`. `coverage report --format=total`
prints a whole number (no `[tool.coverage]` config / `.coveragerc`, no `fail_under`).

## ALGORITHM

```
combine coverage data -> coverage.xml
total = coverage report --format=total      # e.g. "83"
write "total=<n>" to $GITHUB_OUTPUT
if push to main: dynamic-badges-action writes {label: coverage, message: "<n>%", color: blue}
  to gist file mcp_coder-coverage.json      # failure ignored (continue-on-error)
```

## DATA

Gist file content written by the action: shields endpoint JSON
`{"schemaVersion": 1, "label": "coverage", "message": "<n>%", "color": "blue"}`.

## Verification

- Re-read the `coverage` job: badge step has the exact `if`, `continue-on-error: true`, the pinned
  SHA with `# v1.9.0`; no `contents: write` anywhere in `ci.yml`.
- Run `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_pytest_check` (fast unit set
  from CLAUDE.md, with `-n auto`), `mcp__mcp-tools-py__run_mypy_check` — all pass.
- `mcp__mcp-tools-py__run_format_code`, then commit: `ci: publish combined coverage badge to gist`
