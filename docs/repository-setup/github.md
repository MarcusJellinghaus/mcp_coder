# GitHub Setup

GitHub-side configuration: tokens, labels, actions, CI, badges, and automated dependency management.

## GitHub Token Configuration

> **Note:** This is **user-level** configuration in your home directory, not a project file. See the [Configuration Guide](../configuration/config.md) for the full user config schema.

The workflow automation requires a GitHub token configured in your user config file.

**Config file locations:**

| Platform | Config Path |
|----------|-------------|
| **Linux/macOS** | `~/.mcp_coder/config.toml` |
| **Windows** | `%USERPROFILE%\.mcp_coder\config.toml` |

**Token configuration:**

```toml
[github]
token = "ghp_your_github_token_here"
```

**Token options** (either one works):

1. **Fine-grained PAT** (least privilege). Grant repository access to the target repos
   with these read permissions, which are the ones `mcp-coder verify` probes:
   - `Contents: Read`
   - `Administration: Read` (branch protection)
   - `Pull requests: Read`
   - `Issues: Read`
   - `Actions: Read`
   - `Commit statuses: Read`

   `verify` reads branch protection from both classic protection and rulesets.
   Classic protection needs `Administration: Read`; without it, the protection rows
   rely on rulesets alone.
   - A protection found by either source counts and shows `[OK]`.
   - A row shows "not configured" only when both sources answered.
   - If one source can't be read and the other doesn't show the protection, the row
     shows `[WARN] not verifiable` — including when classic protection shows none and
     rulesets can't be read.
   - `[WARN] not verifiable` is not an error, and the exit code is unaffected.

   Effective rules do not expose bypass actors, so "protected" does not mean "nobody
   can bypass".

2. **Classic PAT** (simpler, broader). Use the `repo` scope (`public_repo` covers public
   repositories only). Classic scopes grant permissions in bundles, so a `repo`-scope
   token satisfies all of the checks above.

**How to create:** go to GitHub → Settings → Developer settings → Personal access
tokens, choose *Fine-grained tokens* or *Tokens (classic)*, then add the token to the
config file.

## Repo Security Configuration Checks

> Overview: see [quality-and-security-checks.md](quality-and-security-checks.md).

`mcp-coder verify` prints a `GITHUB SECURITY` section right after `GITHUB`, reporting
— not changing — the repo's security configuration:

```
=== GITHUB SECURITY =======================================================
  Dependabot config      [OK]   .github/dependabot.yml (pip: weekly)
  Dependabot alerts      [OK]   enabled
  Dependabot security    [WARN] security updates disabled
  Secret scanning        [ERR]  disabled
  Secret push protection [ERR]  disabled
  CodeQL workflow        [ERR]  no workflow step uses github/codeql-action
  Code scanning alerts   [WARN] not configured (no CodeQL workflow)
```

Two local-file rows need no token:

- **Dependabot config** reads `.github/dependabot.yml` (or `.yaml`) directly.
- **CodeQL workflow** scans `.github/workflows/*.yml` for a step using
  `github/codeql-action`.

Four rows are API-backed and need `Administration: Read` on the GitHub token (the same
permission already listed in the fine-grained PAT table above) — without it, they show
`[WARN] not accessible` instead of a real on/off state:

- Dependabot alerts
- Dependabot security
- Secret scanning
- Secret push protection

**Code scanning alerts** reflects only whether CodeQL is configured (from the row
above); it does not query real alert counts — that needs a different permission scope
and there is no repo with CodeQL enabled yet to verify it against.

The whole section is report-only and exit-neutral: it never fails the `verify`
command. Turning features on or off happens in the GitHub web UI, not through `verify`.

## Workflow Labels Setup

### About Status Labels

MCP Coder uses **status labels** to track issues through their development lifecycle:

```
status-01:created → status-02:awaiting-planning → ... → status-10:pr-created
```

**Benefits:**

- Visual pipeline tracking in GitHub Issues
- Automated status progression with `/approve` command
- No issues lost without status tracking
- Team visibility into work progress

### Setting Up Labels

**1. Preview labels:**

```bash
mcp-coder gh-tool define-labels --dry-run  # Preview changes
```

**2. Apply labels:**

```bash
mcp-coder gh-tool define-labels            # Create/update labels
```

**3. Verify in GitHub:**

- Go to your repository → Issues → Labels
- Confirm status labels are created with correct colors

### Customizing Labels

**Default label source:** `mcp_coder/config/labels.json`, deployed with the package.

**Custom labels:** Point to a custom `labels.json` via `pyproject.toml`:

```toml
[tool.mcp-coder]
labels-config = "config/labels.json"
```

Alternatively, pass `--config PATH` on the command line. See [`labels_schema.md`](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/src/mcp_coder/config/labels_schema.md) for the schema.

**Test custom config:**

```bash
mcp-coder gh-tool define-labels --dry-run  # Preview your custom labels
```

### Issue Validation and Initialization

Issue initialization and validation are opt-in operations:

**Initialization (`--init`):**

- Assigns the `default: true` label to open issues without any status label
- Use `--dry-run` to preview which issues would be initialized

```bash
mcp-coder gh-tool define-labels --init
```

**Validation (`--validate`):**

- **Errors:** Issues with multiple status labels (requires manual fix)
- **Warnings:** Bot processes exceeding their stale timeout threshold

```bash
mcp-coder gh-tool define-labels --validate
```

**All operations (`--all`):**

Run `--init`, `--validate`, and `--generate-github-actions` together:

```bash
mcp-coder gh-tool define-labels --all
```

### Stale Timeout Configuration

Bot-busy labels can have configurable timeout thresholds in `labels.json`:

```json
{
  "internal_id": "implementing",
  "name": "status-06:implementing",
  "category": "bot_busy",
  "stale_timeout_minutes": 120
}
```

Default timeouts:

| Label | Timeout |
|-------|---------|
| status-03:planning | 15 minutes |
| status-06:implementing | 120 minutes |
| status-09:pr-creating | 30 minutes |
| status-14i:plan-reviewing | 30 minutes |
| status-17i:code-reviewing | 120 minutes |

The `status-14i` / `status-17i` labels are the in-progress states for the optional automated review workflows (enabled via `auto_review_plan` / `auto_review_implementation`).

## Base Branch Support for Issues

### Overview

Issues can specify a base branch to start work from a branch other than the repository default. This is useful for:

- **Hotfixes**: Starting from a release branch
- **Feature chains**: Building on existing feature work
- **Release preparation**: Working from release branches

### Issue Body Format

Add a `### Base Branch` section to your issue body:

```markdown
### Base Branch

feature/existing-work

### Description

The actual issue content...
```

### Parsing Rules

- **Case-insensitive**: `Base Branch`, `base branch`, `BASE BRANCH` all work
- **Any heading level**: `#`, `##`, `###` all work
- **Single line only**: a multi-line value is rejected on write by mcp-workspace; otherwise it is ignored (see [Trust and Validation](#trust-and-validation))
- **Valid git ref name**: see [Trust and Validation](#trust-and-validation)
- **Whitespace trimmed**: Leading/trailing whitespace is ignored
- **Empty = fallback**: if the section is empty, missing, untrusted or malformed, the fallback in [Trust and Validation](#trust-and-validation) applies

### Trust and Validation

The section is honoured only when the issue body is trusted:

- **Trusted body**: the author is trusted (`OWNER`, `MEMBER`, `COLLABORATOR`, or listed in `[github] trusted_commenters`), **or** the last body editor is the token user or listed in `trusted_commenters`. Full rule: mcp-workspace README, [Commenter trust](https://github.com/MarcusJellinghaus/mcp-workspace#commenter-trust); config key: [GitHub configuration](https://github.com/MarcusJellinghaus/mcp-workspace#github-configuration).
  - Editor trust has no role check: a collaborator editing a stranger's issue does not make it trusted unless they are in `trusted_commenters`.
  - If the untrusted author edits the body again, they become the last editor and the section is ignored again.
- **Untrusted → ignored entirely**: no value, no error, no Review Gate block. Tool output does not mention it; only a log line records it.
- **Ref-name rule**: the value must be a valid git ref name ([`git check-ref-format`](https://git-scm.com/docs/git-check-ref-format)): no spaces or control characters; no `..`, `~`, `^`, `:`, `?`, `*`, `[`, `\`, `@{` or `//`; no leading `-` or `.`; no trailing `.`, `/` or `.lock`.
- **Malformed** (multiple lines or an invalid ref name) in a trusted issue: mcp_coder commands ignore it silently, as if it were untrusted. Only mcp-workspace tools report it: the `check_branch_status` MALFORMED line / Review Gate, and `get_base_branch`.
- **Workflows**: GitHub Actions that change labels apply the same trusted set; see [Label-Changing Workflows Must Gate on Author Trust](#label-changing-workflows-must-gate-on-author-trust).

**Fallback** when there is no usable section (missing, empty, untrusted or malformed):

- **Base branch detection** — `gh-tool get-base-branch`, `rebase`, the implement workflow's rebase step, `fix-conflict`, `git-tool`, create-pr, review — falls through to the open PR's base → git merge-base → default branch. For `mcp-coder rebase`, a result other than `main`/`master` needs `--base-branch`.
- **Branch creation** — `create-plan`, `gh-tool checkout-issue-branch` — starts from the default branch.

### Validation

The base branch is validated at branch creation time:

- If the branch doesn't exist, branch creation fails with a clear error
- The `/issue_analyse` command will warn if the specified branch doesn't exist
- mcp-workspace's `github_issue_create` / `github_issue_edit` reject a multi-line or invalid ref-name value on write (unless the server runs with `--no-enforce-base-branch-format`)

create-plan, create-pr, `mcp-coder rebase` and the implement workflow's rebase step all check that the base branch exists on origin and report a clear error — except the implement step, which only warns and skips the rebase.

### Epic Branches

An epic is delivered on its own branch (e.g. `epic/multi-language`), merged to main last.

1. Create and push the epic branch from main: `git checkout -b epic/<name> origin/main`, then `git push -u origin epic/<name>`.
2. Add `### Base Branch` with `epic/<name>` to each sub-issue. create-plan, implement, `mcp-coder rebase`, review and create-pr then use it without flags — provided the sub-issue body is trusted (written by a trusted author, or last edited by the token user or an allowlisted login; see [Trust and Validation](#trust-and-validation)).
3. Sub-PRs target and merge into the epic branch.
4. Finish by opening the epic-to-main PR manually — `mcp-coder create-pr` does not apply, since the epic branch has no issue number. GitHub does not auto-close issues on merges to a non-default branch, so the PR body must list every sub-issue with `Closes #N` (`Closes owner/repo#N` for other repos).
5. Multi-repo epics: a base branch is resolved in the sub-issue's own repo, so create one epic branch per repo, ideally with the same name.
6. Rebasing the epic branch onto main rewrites its history. Rebase each open sub-branch onto the new tip manually: `git rebase --onto <new-epic-tip> <old-epic-tip>`.

### Backward Compatibility

Existing issues without a `### Base Branch` section — or whose section is ignored because the body is untrusted or the value is malformed — fall back as described in [Trust and Validation](#trust-and-validation): detection falls back to the PR base, merge-base or default branch, and branch creation uses the repository's default branch (typically `main` or `master`).

### Example Issues

**Issue with base branch:**

```markdown
### Base Branch

release/2.0

### Description

Fix critical bug in release 2.0

### Acceptance Criteria

- Bug is fixed
- Tests pass
```

**Issue without base branch (uses default):**

```markdown
### Description

Add new feature to main branch

### Acceptance Criteria

- Feature works
- Tests pass
```

## GitHub Actions Setup

### Required Actions

> **Tip:** You can generate these workflow files automatically:
> ```bash
> mcp-coder gh-tool define-labels --generate-github-actions
> ```
> This writes `label-new-issues.yml` and `approve-command.yml` to `.github/workflows/` based on your label config.

> Existing repositories: re-run `mcp-coder gh-tool define-labels --generate-github-actions` to pick up the `/approve` trust gate, `permissions: {}` and the pinned action.

Alternatively, set up these two workflows manually:

#### 1. Auto-Label New Issues

Create `.github/workflows/label-new-issues.yml`:

```yaml
name: Label New Issues

on:
  issues:
    types: [opened]

permissions: {}

jobs:
  add-label:
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Add status label
        uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3 # v9.0.0
        with:
          script: |
            github.rest.issues.addLabels({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: ['status-01:created']
            });
```

**Purpose:** Automatically adds `status-01:created` label to new issues.

#### 2. Approve Command Handler

Create `.github/workflows/approve-command.yml`:

```yaml
name: Approve Command

on:
  issue_comment:
    types: [created]

permissions: {}

jobs:
  handle-approve:
    runs-on: ubuntu-latest
    # Only run on issues (not PRs), when comment contains /approve, and only for trusted commenters (OWNER/MEMBER/COLLABORATOR); untrusted -> skipped silently
    if: github.event.issue.pull_request == null && contains(github.event.comment.body, '/approve') && contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.comment.author_association)
    permissions:
      issues: write
    steps:
      - name: Handle approve command
        uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3 # v9.0.0
        with:
          script: |
            const comment = context.payload.comment.body.trim();

            // Only process if comment is exactly /approve
            if (comment !== '/approve') {
              return;
            }

            const issue = context.payload.issue;
            const labels = issue.labels.map(l => l.name);

            // Define the promotion paths: [current_status, next_status]
            const promotions = {
              'status-01:created': 'status-02:awaiting-planning',
              'status-04:plan-review': 'status-05:plan-ready',
              'status-07:code-review': 'status-08:ready-pr',
            };

            let promoted = false;
            let oldStatus = null;
            let newStatus = null;

            // Check which status the issue currently has and promote it
            for (const [currentStatus, nextStatus] of Object.entries(promotions)) {
              if (labels.includes(currentStatus)) {
                // Remove old status
                await github.rest.issues.removeLabel({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issue.number,
                  name: currentStatus
                }).catch(() => {}); // Ignore errors if label doesn't exist

                // Add new status
                await github.rest.issues.addLabels({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issue.number,
                  labels: [nextStatus]
                });

                oldStatus = currentStatus;
                newStatus = nextStatus;
                promoted = true;
                break;
              }
            }

            // Post confirmation comment
            if (promoted) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                body: `✅ Status promoted: \`${oldStatus}\` → \`${newStatus}\`\n\nThe bot can now pick up this issue for the next step.`
              });
            } else {
              // No matching status found
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                body: `⚠️ Cannot promote issue. The issue must have one of these statuses:\n- \`status-01:created\`\n- \`status-04:plan-review\`\n- \`status-07:code-review\`\n\nCurrent labels: ${labels.filter(l => l.startsWith('status-')).join(', ') || 'none'}`
              });
            }
```

**Purpose:** Handles `/approve` comments to promote issues through workflow stages.

### Label-Changing Workflows Must Gate on Author Trust

Any workflow that changes labels on behalf of a comment or event author must gate on `author_association` (`OWNER`, `MEMBER`, `COLLABORATOR`), e.g.:

`if: contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.comment.author_association)`

**Why:** GitHub restricts label edits to users with triage access or higher, but a workflow runs with `GITHUB_TOKEN` write access and bypasses that restriction. Without the gate, any GitHub user could move an issue through the bot pipeline. The generated `approve-command.yml` applies this gate.

### Installing Actions

```bash
# 1. Create directories
mkdir -p .github/workflows

# 2. Add workflow files (copy YAML content above)

# 3. Commit and push
git add .github/workflows/
git commit -m "Add GitHub Actions for issue workflow automation"
git push
```

**Verify in GitHub:** Go to repository → Actions tab → Confirm workflows appear.

## Code Quality CI

> Overview: see [quality-and-security-checks.md](quality-and-security-checks.md).

> **Customize (`.github/workflows/ci.yml`):** Python version, package name, and test paths.

Add comprehensive CI checks to your GitHub Actions workflow.

> **Note:** The example below uses Python tools (ruff, pytest, mypy, etc.). For Python-specific matrix details, see [python.md](python.md#ci-workflow-for-python).

### CI Workflow Example

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: ["*"]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        check:
          - {name: "ruff", cmd: "ruff version && ruff check src tests tools"}
          - {name: "ruff-format", cmd: "ruff version && ruff format --check src tests tools"}
          - {name: "pylint", cmd: "pylint -E ./src ./tests"}
          - {name: "pytest", cmd: "pytest"}
          - {name: "mypy", cmd: "mypy --strict src tests"}
    name: ${{ matrix.check.name }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: ${{ matrix.check.cmd }}

  # Architecture checks (PR only)
  architecture:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    strategy:
      fail-fast: false
      matrix:
        check:
          - {name: "import-linter", cmd: "lint-imports"}
          - {name: "tach", cmd: "tach check"}
          - {name: "pycycle", cmd: "pycycle --here"}
          - {name: "vulture", cmd: "vulture src tests --min-confidence 60"}
          - {name: "deptry", cmd: "deptry src"}
    name: ${{ matrix.check.name }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: ${{ matrix.check.cmd }}
```

### Monitor CI Results

Use [`mcp-coder check branch-status`](../cli-reference.md) to monitor CI pipeline results and get comprehensive feedback on code quality checks.

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

### Scorecard and CodeQL badges

`.github/workflows/scorecard.yml` needs no secrets: it publishes results for the Scorecard badge and
uploads SARIF to code scanning. The CodeQL badge reflects CodeQL default setup (no workflow file).

## Automated Dependency Management

- **Purpose:** Security updates and dependency monitoring
- **Documentation:** [Dependabot documentation](https://docs.github.com/en/code-security/dependabot)
- **Reference:** See `.github/dependabot.yml` in this repository
