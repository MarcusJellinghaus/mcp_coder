# Summary — Issue #1291: README badges (metadata, tool badges, live coverage, OpenSSF Scorecard, CodeQL)

## Goal

Make the project's CI and security posture visible with three badge lines under the `# MCP Coder`
title. Pass/fail comes from the CI workflow badge; tool badges are static; coverage is the only live
quality number; OpenSSF Scorecard + CodeQL show security posture.

All values (action SHAs, gist ID, badge URLs, verified build config) come verbatim from issue #1291.
Do not resolve, probe or change any of them. The implementer has no Bash.

## Architectural / design changes

No Python code changes. Changes are repository metadata, CI configuration and docs:

1. **License metadata (PEP 639).** A real `LICENSE` file replaces the classifier-only MIT
   declaration. `pyproject.toml` declares `license = "MIT"` + `license-files`; the build backend
   floor rises to `setuptools>=77`; the `License ::` classifier is removed (it makes the build
   fail under PEP 639). Effects: `github/license` badge and Scorecard *License* check work; wheel
   metadata gains `License-Expression: MIT`.
2. **Live coverage badge via gist.** The existing `coverage` job in `ci.yml` already combines unit +
   integration + langchain data. It now also writes the total to a step output (inside the existing
   `Combine coverage data` step — no new capture step), and a new badge step pushes it to a shared
   public gist via `schneegans/dynamic-badges-action`.
   - Runs on `push` to `main` only (fork PRs never see the secret).
   - `continue-on-error: true` — a badge write never fails CI.
   - Auth: fine-grained PAT limited to Gists (`secrets.BADGE_GIST_TOKEN`); gist ID from
     `vars.BADGE_GIST_ID`. No job gains `contents: write`.
   - No other `ci.yml` change (no new jobs, no renames → no ruleset change).
3. **OpenSSF Scorecard workflow (new).** `scorecard.yml` runs on push to `main`, weekly, and on
   `branch_protection_rule`; publishes results (feeds the Scorecard badge) and uploads SARIF to code
   scanning. Minimal upstream template, least-privilege job permissions. Not a required check.
4. **README badges.** Three Markdown paragraphs (separated by blank lines) of `[![alt](img)](link)`.
5. **Docs.** New `## README Badges` section in `docs/repository-setup/github.md`; shared-files table
   and detail-docs table updates in `docs/repository-setup/README.md`.

Known side effect (out of scope, tracked in #1163): `verify`'s *CodeQL workflow* row turns OK because
`scorecard.yml` contains `uses: github/codeql-action/...`.

## TDD note

This change is configuration and documentation only — there is no Python behaviour to test, and the
issue explicitly rejects adding a build-verification job. Each step's verification is: re-read the
changed file(s) against the step's checklist, then run the standard checks (pylint, pytest fast unit
set, mypy) to confirm nothing regressed.

## Files created / modified

| File | Action | Step |
|---|---|---|
| `LICENSE` | create | 1 |
| `pyproject.toml` | modify (`[build-system]`, `[project]`) | 1 |
| `.github/workflows/ci.yml` | modify (`coverage` job) | 2 |
| `docs/repository-setup/github.md` | modify (intro line, new `## README Badges` section) | 2, 3 |
| `docs/repository-setup/README.md` | modify (two tables) | 2, 3 |
| `.github/workflows/scorecard.yml` | create | 3 |
| `README.md` | modify (badge lines under title) | 4 |

No new folders or Python modules.

## Steps

| Step | Content | Commit |
|---|---|---|
| [step_1.md](step_1.md) | `LICENSE` + PEP 639 license metadata | `build: add MIT LICENSE and PEP 639 license metadata` |
| [step_2.md](step_2.md) | Coverage badge in `ci.yml` + `README Badges` docs | `ci: publish combined coverage badge to gist` |
| [step_3.md](step_3.md) | `scorecard.yml` + docs | `ci: add OpenSSF Scorecard workflow` |
| [step_4.md](step_4.md) | README badge lines | `docs(readme): add metadata, tooling and security badges` |

## Action pins (verbatim from the issue)

| Action | Pin |
|---|---|
| `actions/checkout` (scorecard.yml only) | `3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` |
| `ossf/scorecard-action` | `fa7117db83c52d787ae5a89f350999701505d78e # v2.5.0` |
| `github/codeql-action/upload-sarif` | `9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1` |
| `schneegans/dynamic-badges-action` | `28b0fa8bdeb46170ac397105ece0c1fe58f68910 # v1.9.0` |

Gist ID: `9a7892066964f11765a07d74285ad104`. Gist file: `mcp_coder-coverage.json`.
