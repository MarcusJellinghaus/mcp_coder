# Summary — #1354 CI: first-line checks on push, backup checks on PRs, full set on main

## Goal

Restructure `.github/workflows/ci.yml` by event, so each check runs at least once before merge
without most of today's duplicate push + PR runs.

- **First-line checks** (fast, catch most errors early) run on feature-branch push.
- **Backup checks** (slow, or redundant with earlier gates) run on the PR.
- **Main push / dispatch** runs both sets (post-merge safety net).

## Architectural / design changes

No Python code changes. CI layout change only:

| Job | Feature push | PR | Main push / dispatch |
|---|---|---|---|
| ruff-format, ruff, mypy, file-size, no-url-deps, forbidden-calls, **vulture**, **import-linter** | ✅ | — | ✅ |
| unit-tests, integration-tests | ✅ | ✅ | ✅ |
| **pylint**, **tach**, **deptry**, **vscodeclaude-template-install** | — | ✅ | ✅ |
| check-forbidden-folders | — | ✅ | — |
| langchain-integration, coverage | — | ✅ | main push only (unchanged) |

Bold = changed from today.

Mechanics (in `ci.yml`):

- The `test` matrix is renamed to **`push-checks`** (`if: github.event_name != 'pull_request'`).
  It loses `pylint` and gains `vulture` and `import-linter`.
- The `architecture` matrix is renamed to **`pr-checks`**
  (`if: github.event_name != 'push' || github.ref == 'refs/heads/main'`). It loses `vulture` and
  `import-linter` and gains `pylint`. It moves to sit directly after `push-checks`.
- Two matrices are needed because a job-level `if` cannot read `matrix`. A step-level `if` is
  forbidden: the job would report "passed".
- Matrix entry `name`s are unchanged: they are required-check names.
- `vscodeclaude-template-install` gets the same `if:` as `pr-checks`.
- `unit-tests` and `integration-tests` have no condition. `check-forbidden-folders`,
  `langchain-integration`, `coverage` and the triggers are unchanged.
- Short comments record the rule in `ci.yml`. Per-check rationale lives in
  `docs/repository-setup/quality-and-security-checks.md` (new `## CI events` section).

Consequences (accepted in the issue):

- Review's CI-fix loop now sees vulture and import-linter. pylint, tach, deptry and
  template-install failures surface after `create-pr`, via `fix-ci`.

## KISS decisions

- **One step, one commit.** The YAML change and the docs describe the same layout, so they
  are not independent. Splitting them would leave the docs wrong for one commit.
- No YAML anchors or other de-duplication of the job steps: not in scope, and a new idiom.
- `CI events` is one table with a **Why** column, not a table plus a separate rationale list.
  Other doc sections link to it instead of repeating event facts.
- No Python is touched, so there are no unit tests to write (TDD not applicable). No MCP tool
  validates workflow YAML; the first CI run on the branch is the syntax check.

## Files modified

| File | Change |
|---|---|
| `.github/workflows/ci.yml` | `test` → `push-checks`, `architecture` → `pr-checks`, entries moved, `if:` conditions, comments |
| `docs/repository-setup/quality-and-security-checks.md` | New `## CI events` section; fix Architecture and Dependencies sentences |
| `docs/repository-setup/github.md` | CI template: pointer comment; move `import-linter` and `vulture` into `test` matrix |

No files or folders created (besides `pr_info/`, which is removed before merge by the workflow).

Out of scope: `docs/architecture/architecture.md` (no push/PR facts); broader `github.md`
refresh (#1351); CI fixing in `create-pr` (#1286).

## Manual verification (not an implement task)

After the PR is open: check that a failing `push-checks` job blocks the PR (required-check
behaviour with skipped matrix jobs is unverified, see #1294).
