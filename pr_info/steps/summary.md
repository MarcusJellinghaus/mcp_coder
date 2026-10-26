# Summary — #1310 OpenSSF Scorecard quick wins

Part of epic #1163. Covers tasks 1–6 of the issue. Task 7 (ruleset / branch protection) and task 8 (SAST re-check) are manual maintainer work with no code change.

## Goals

| Task | Outcome |
|---|---|
| 1 Security-Policy | `SECURITY.md` at repo root; listed in the shared-files table |
| 2 `/approve` trust gate | Generated `approve-command.yml` job runs only for `OWNER`/`MEMBER`/`COLLABORATOR` commenters |
| 3 Token-Permissions | Both generated workflows have top-level `permissions: {}` |
| 4 Label-workflow rule | Documented in `docs/repository-setup/github.md` § GitHub Actions Setup, linked from "Trust and Validation" |
| 5 Pinned-Dependencies | Every `uses:` in `.github/workflows/*.yml` is `@<40-hex-sha> # vX.Y.Z` |
| 6 Signed-Releases | `publish.yml` attaches `dist/*` + `provenance.sigstore.json` to the GitHub release |

## Architectural / design changes

- **The generator stays the single source of truth** for `label-new-issues.yml` and `approve-command.yml`. Every change to these files is made in the templates in `define_labels_actions.py`. The committed files and both doc snippets are exact copies of the generator output, and **a new consistency test enforces this**.
- **One pinned action reference.** A module constant `_GITHUB_SCRIPT_REF` (`actions/github-script@<sha> # v9.0.0`) is used by both templates. Generated workflows in downstream repos then stay current through those repos' own Dependabot.
- **Trust gate at the job level.** The `if:` check on `author_association` skips the job silently for untrusted commenters, with no reply comment. The script keeps its exact-match `/approve` check, because expressions can't trim whitespace.
- **Least-privilege tokens.** The top-level `permissions: {}` sets every scope to none; each job grants only what it needs (`issues: write`).
- **Signing runs in a separate release job.** `attach-signed-artifacts` (`needs: publish`) signs keylessly with Sigstore through `actions/attest-build-provenance`. The PyPI job keeps only `id-token: write`, the bundle never lands in `dist/`, and a failure in this job can't affect the PyPI release.
- No new modules, no new runtime dependencies, no change to the CLI interface.

### Known maintenance interaction (accepted)
When Dependabot bumps `actions/github-script` in the committed generated files, the consistency test fails until `_GITHUB_SCRIPT_REF` (and the two doc snippets) are updated in the same PR. This is intentional: it makes sure the generator gets the bump too.

## Resolved action pins (from `git ls-remote`, peeled commit SHAs)

| Action | Version | SHA |
|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-python` | v7.1.0 | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` |
| `astral-sh/setup-uv` | v7.6.0 | `37802adc94f370d6bfd71619e3f0bf239e1f3b78` |
| `actions/upload-artifact` | v7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| `actions/download-artifact` | v8.0.2 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` |
| `pypa/gh-action-pypi-publish` | v1.14.3 | `7245906fb61fa33a13554f9d5fb856fe61758086` |
| `actions/attest-build-provenance` | v4.2.2 | `4d101475d8b20a2381f78447822ac1eab6504dd8` |
| `actions/github-script` | v9.0.0 | `3a2844b7e9c422d3c10d287c895573f7108da1b3` |

Pin format: `uses: <owner>/<repo>@<sha> # <version>`, e.g. `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`.

## Files created / modified

| File | Change | Step |
|---|---|---|
| `src/mcp_coder/cli/commands/define_labels_actions.py` | `_GITHUB_SCRIPT_REF`, `permissions: {}`, trust gate, `\n\n` separator | 1 |
| `tests/cli/commands/test_define_labels_actions.py` | gate / permissions / SHA-pin tests (step 1); consistency test (step 2) | 1, 2 |
| `.github/workflows/approve-command.yml` | regenerated | 2 |
| `.github/workflows/label-new-issues.yml` | regenerated | 2 |
| `docs/repository-setup/github.md` | snippets replaced with generator output, re-run note (step 2); label-workflow rule plus link from Trust and Validation (step 3) | 2, 3 |
| `docs/getting-started/label-setup.md` | snippets replaced with generator output, re-run note | 2 |
| `SECURITY.md` (new) | security policy | 4 |
| `docs/repository-setup/README.md` | `SECURITY.md` row in the shared-files table | 4 |
| `.github/workflows/ci.yml` | SHA pins (26) | 5 |
| `.github/workflows/upstream-compat-check.yml` | SHA pins (3) | 5 |
| `.github/workflows/publish.yml` | SHA pins (5) (step 5); `attach-signed-artifacts` job (step 6) | 5, 6 |

Not touched: `scorecard.yml` (already pinned) and the Code Quality CI example in `github.md` (`@v4`, out of scope).

## Steps

1. [step_1.md](step_1.md) — Generator: pin, permissions, trust gate, separator (TDD)
2. [step_2.md](step_2.md) — Regenerate committed workflows, replace doc snippets, consistency test
3. [step_3.md](step_3.md) — Document the label-workflow rule
4. [step_4.md](step_4.md) — `SECURITY.md` and shared-files table row
5. [step_5.md](step_5.md) — SHA-pin the non-generated workflows
6. [step_6.md](step_6.md) — Signed release assets job

Each step is one commit. After each step run pylint, pytest (`-n auto`, unit markers), mypy, then `run_format_code`.
